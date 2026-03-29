from typing import Literal

from pydantic import BaseModel, Field


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatHistoryMessage] | None = None


class CardToCreate(BaseModel):
    column_id: int
    title: str = Field(min_length=1)
    details: str = ""
    position: int | None = None


class CardToUpdate(BaseModel):
    card_id: int
    title: str | None = None
    details: str | None = None
    column_id: int | None = None
    position: int | None = None


class CardToDelete(BaseModel):
    card_id: int


class CardToMove(BaseModel):
    card_id: int
    column_id: int
    position: int = Field(ge=0)


class BoardUpdate(BaseModel):
    cards_to_create: list[CardToCreate] = Field(default_factory=list)
    cards_to_update: list[CardToUpdate] = Field(default_factory=list)
    cards_to_delete: list[CardToDelete] = Field(default_factory=list)
    cards_to_move: list[CardToMove] = Field(default_factory=list)


class AIResponse(BaseModel):
    message: str
    board_update: BoardUpdate | None = None
