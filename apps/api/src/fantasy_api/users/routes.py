"""`/me`, and the owner's `/invites` and `/members` (APP-008). The acting user always comes from the
verified token (`current_user`), never from the request body, query or other headers."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response, status

from fantasy_api import schemas
from fantasy_api.auth import current_user, require_owner
from fantasy_api.users.model import Invite, User
from fantasy_api.users.service import UserService

router = APIRouter(tags=["users"])
Owner = Annotated[User, Depends(require_owner)]


def service_of(request: Request) -> UserService:
    users: UserService = request.app.state.users
    return users


Users = Annotated[UserService, Depends(service_of)]


def _invite(invite: Invite, users: UserService) -> schemas.Invite:
    state: Literal["open", "expired", "claimed"] = (
        "claimed"
        if invite.claimed_by is not None
        else "expired"
        if invite.expired(users.clock.now())
        else "open"
    )
    return schemas.Invite(
        id=invite.id,
        email=invite.email,
        role=invite.role,
        created_by=invite.created_by,
        created_at=invite.created_at,
        expires_at=invite.expires_at,
        claimed_by=invite.claimed_by,
        claimed_at=invite.claimed_at,
        status=state,
    )


@router.get("/me")
def me(user: Annotated[User, Depends(current_user)]) -> schemas.Me:
    return schemas.Me(
        uid=user.uid, email=user.email, display_name=user.display_name, role=user.role
    )


@router.post(
    "/invites",
    status_code=status.HTTP_201_CREATED,
    responses={200: {"description": "An open invite for this email already existed"}},
)
def create_invite(
    body: schemas.InviteCreate, owner: Owner, users: Users, response: Response
) -> schemas.Invite:
    invite, created = users.invite(owner, body.email, body.role)
    if not created:
        response.status_code = status.HTTP_200_OK
    return _invite(invite, users)


@router.get("/invites")
def list_invites(_: Owner, users: Users) -> list[schemas.Invite]:
    return [_invite(i, users) for i in users.invites()]


@router.delete("/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invite(invite_id: str, _: Owner, users: Users) -> None:
    users.revoke_invite(invite_id)


@router.get("/members")
def list_members(_: Owner, users: Users) -> list[schemas.Member]:
    return [
        schemas.Member(
            uid=u.uid,
            email=u.email,
            display_name=u.display_name,
            role=u.role,
            created_at=u.created_at,
            last_seen_at=u.last_seen_at,
        )
        for u in users.members()
    ]


@router.delete("/members/{uid}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(uid: str, _: Owner, users: Users) -> None:
    users.remove_member(uid)
