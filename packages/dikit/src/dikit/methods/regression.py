"""Small, dependency-free regressors: closed-form ridge and class-weighted L2 logistic (Newton)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

NEWTON_TOL = 1e-8


class Regressor(Protocol):
    def fit(self, x: np.ndarray, y: np.ndarray) -> Regressor: ...
    def predict(self, x: np.ndarray) -> np.ndarray: ...


@dataclass
class Ridge:
    """Ridge regression on standardised features (closed form); alpha fixed a priori."""

    alpha: float = 10.0
    coef_: np.ndarray | None = None
    mu_: np.ndarray | None = None
    sd_: np.ndarray | None = None
    b0_: float = 0.0

    def fit(self, x: np.ndarray, y: np.ndarray) -> Ridge:
        self.mu_, self.sd_ = x.mean(axis=0), x.std(axis=0)
        self.sd_[self.sd_ == 0] = 1.0
        z = (x - self.mu_) / self.sd_
        self.b0_ = float(y.mean())
        self.coef_ = np.linalg.solve(
            z.T @ z + self.alpha * np.eye(z.shape[1]), z.T @ (y - self.b0_)
        )
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        if self.coef_ is None or self.mu_ is None or self.sd_ is None:
            msg = "Ridge.predict called before fit"
            raise RuntimeError(msg)
        return np.asarray(self.b0_ + ((x - self.mu_) / self.sd_) @ self.coef_)


@dataclass
class Logistic:
    """L2 logistic regression (Newton), class-weighted [R-89], intercept prior-corrected."""

    l2: float = 1.0
    coef_: np.ndarray | None = None
    mu_: np.ndarray | None = None
    sd_: np.ndarray | None = None

    def fit(self, x: np.ndarray, y: np.ndarray) -> Logistic:
        self.mu_, self.sd_ = x.mean(axis=0), x.std(axis=0)
        self.sd_[self.sd_ == 0] = 1.0
        z = np.column_stack([np.ones(len(y)), (x - self.mu_) / self.sd_])
        pos = max(float(y.sum()), 1.0)
        w_pos = (len(y) - pos) / pos
        wts = np.where(y == 1, w_pos, 1.0)
        beta = np.zeros(z.shape[1])
        pen = self.l2 * np.eye(z.shape[1])
        pen[0, 0] = 0.0
        for _ in range(50):
            p = 1 / (1 + np.exp(-(z @ beta)))
            grad = z.T @ (wts * (p - y)) + pen @ beta
            hess = (z * (wts * p * (1 - p))[:, None]).T @ z + pen
            step = np.linalg.solve(hess, grad)
            beta -= step
            if np.abs(step).max() < NEWTON_TOL:
                break
        beta[0] -= np.log(w_pos)  # undo the class weight's shift of the log-odds (prior correction)
        self.coef_ = beta
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if self.coef_ is None or self.mu_ is None or self.sd_ is None:
            msg = "Logistic.predict_proba called before fit"
            raise RuntimeError(msg)
        z = np.column_stack([np.ones(len(x)), (x - self.mu_) / self.sd_])
        return np.asarray(1 / (1 + np.exp(-(z @ self.coef_))))
