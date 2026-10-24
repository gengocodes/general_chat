"""Domain stream events emitted during agent processing."""

from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field

ActivityStatus = Literal["started", "completed"]


class StreamActivityEvent(BaseModel):
    """Event emitted for milestone activity lifecycle"""

    type: Literal["activity"] = "activity"
    id: str
    message: str
    status: ActivityStatus


class StreamTokenEvent(BaseModel):
    """Event emitted for each streamed response token"""

    type: Literal["token"] = "token"
    token: str


class StreamErrorEvent(BaseModel):
    """Event emitted when an error occurs during streaming"""

    type: Literal["error"] = "error"
    error: str


class StreamCompleteEvent(BaseModel):
    """Event emitted when streaming completes successfully"""

    type: Literal["complete"] = "complete"


AgentStreamEvent = Annotated[
    Union[
        StreamActivityEvent,
        StreamTokenEvent,
        StreamErrorEvent,
        StreamCompleteEvent,
    ],
    Field(discriminator="type"),
]
