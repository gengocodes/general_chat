"""Presentation schemas for authentication requests and responses."""

from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):
    """Google ID token (credential) returned by Google Identity Services."""

    credential: str = Field(..., min_length=1, max_length=4096)


class UserResponse(BaseModel):
    """Public profile of the signed-in user."""

    id: str
    email: str
    name: str


class SessionResponse(BaseModel):
    """Authentication state of the current browser session.

    `user` is null for guests. `login_required` is true when a guest has used all free messages.
    """

    user: UserResponse | None
    login_required: bool
