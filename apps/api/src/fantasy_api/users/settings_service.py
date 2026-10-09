"""Settings, Telegram linking, export and self-deletion over a `UserStore` (APP-009).

Every change is a compare-and-set on the settings version, so two tabs (or a tab and the Telegram
webhook) can't silently overwrite each other.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from dikit.time.clock import Clock
from fantasy_api.errors import ApiProblem
from fantasy_api.users.draft_settings import DraftDoc, validate
from fantasy_api.users.settings import (
    DEFAULTS,
    LINK_CODE_TTL,
    LinkCode,
    Settings,
    apply,
    new_link_code,
)
from fantasy_api.users.store import UserStore

LINK_RETRIES = 3  # a link racing a settings save retries on the fresh version


class StaleSettingsError(Exception):
    """The caller's version is not the stored one; `current` is what is stored now."""

    def __init__(self, current: Settings) -> None:
        super().__init__("stale settings")
        self.current = current


class StaleDraftSettingsError(Exception):
    """The caller's version is not the stored one; `current` is what is stored now."""

    def __init__(self, current: DraftDoc) -> None:
        super().__init__("stale draft settings")
        self.current = current


@dataclass
class SettingsService:
    store: UserStore
    clock: Clock

    def get(self, uid: str) -> Settings:
        return self.store.get_settings(uid) or DEFAULTS

    def update(self, uid: str, expected_version: int, changes: dict[str, object]) -> Settings:
        """The validated changes, saved; raises `InvalidSettingError` or `StaleSettingsError`."""
        current = self.get(uid)
        updated = apply(current, changes)  # validate first: a bad field is a 422 even when stale
        if current.version != expected_version or not self.store.save_settings_if(
            uid, updated, expected_version
        ):
            raise StaleSettingsError(self.get(uid))
        return updated

    def get_draft(self, uid: str) -> DraftDoc:
        return self.store.get_draft_settings(uid) or DraftDoc()

    def update_draft(self, uid: str, expected_version: int, raw: object) -> DraftDoc:
        """The validated document, saved as the next version; raises `DraftSettingsError` or
        `StaleDraftSettingsError`."""
        data = validate(raw)  # a bad field is a 422 even when stale
        current = self.get_draft(uid)
        updated = DraftDoc(version=current.version + 1, data=data)
        if current.version != expected_version or not self.store.save_draft_settings_if(
            uid, updated, expected_version
        ):
            raise StaleDraftSettingsError(self.get_draft(uid))
        return updated

    def new_link_code(self, uid: str) -> LinkCode:
        code = LinkCode(new_link_code(), uid, self.clock.now() + LINK_CODE_TTL)
        self.store.save_link_code(code)
        return code

    def link_telegram(self, code: str, chat_id: str) -> Literal["linked", "invalid", "busy"]:
        """Binds the chat to the code's user (replacing any earlier chat). "invalid": the code is
        unknown, used, expired, or its user was removed; "busy": settings kept changing meanwhile
        (the code is spent, so the user asks for a new one, told why)."""
        found = self.store.use_link_code(code.strip().upper(), self.clock.now())
        if found is None or self.store.get_user(found.uid) is None:
            return "invalid"
        for _ in range(LINK_RETRIES):
            current = self.get(found.uid)
            linked = replace(current, telegram_chat_id=chat_id, version=current.version + 1)
            if self.store.save_settings_if(found.uid, linked, current.version):
                return "linked"
        return "busy"

    def delete_me(self, uid: str) -> None:
        result = self.store.delete_user_keeping_an_owner(uid)  # the user and their settings
        if result == "last-owner":
            raise ApiProblem(
                409,
                "last-owner",
                "The last owner can't delete their account",
                "Make another member an owner first.",
            )
