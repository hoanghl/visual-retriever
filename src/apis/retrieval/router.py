# coding: utf-8

from typing import List, Optional, Tuple, Union

from fastapi import APIRouter, Body, Query, WebSocket
from pydantic import Field, StrictBytes, StrictStr
from typing_extensions import Annotated

from .model import KeywordSuggestion, NearestItem

router = APIRouter(tags=["Retrieval"], prefix="/retrieval")


# =================================================
# Image-based retrieval
# =================================================


@router.post(
    "/image",
    responses={
        200: {"model": List[NearestItem], "description": "Successful Response"},
    },
    summary="Get top k similar resources via queried image",
    response_model_by_alias=True,
)
async def retrieval_image_post(
    topk: Optional[Annotated[int, Field(strict=True, ge=0)]] = Query(2, description="", alias="topk", ge=0),
    body: Optional[Union[StrictBytes, StrictStr, Tuple[StrictStr, StrictBytes]]] = Body(None, description=""),
) -> List[NearestItem]:
    # TODO: HoangLe [Jul-20]: Implement this
    ...


# =================================================
# Text-based retrieval
# =================================================


@router.websocket(
    "/keyword",
)
async def retrieval_keyword_get(websocket: WebSocket) -> List[NearestItem]:
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_json(
            [
                KeywordSuggestion(suggestion="a"),
                KeywordSuggestion(suggestion="b"),
                KeywordSuggestion(suggestion="c"),
            ]
        )


@router.get(
    "/text",
    responses={
        200: {"model": List[NearestItem], "description": "Successful Response"},
        400: {"model": object, "description": "Error with query"},
    },
    summary="Get top k resources via input text or selected keywords",
    response_model_by_alias=True,
)
async def retrieval_text_get(
    text: Optional[Annotated[str, Field(strict=False)]] = Query(
        None, description="Full query text from user", alias="text"
    ),
    keywords: Optional[Annotated[list[int], Field(strict=False)]] = Query(
        None, description="List of keyword IDs selected by user", alias="keywords"
    ),
    topk: Optional[Annotated[int, Field(strict=False, ge=0)]] = Query(5, description="", alias="topk", ge=0),
) -> List[NearestItem]:
    # TODO: HoangLe [Sep-13]: Implement this:

    # if text is None and keywords is None:
    #     raise HTTPException(400, "Either 'text' or 'keywords' must be available")

    # Receive text or keywords and
    ...
