# coding: utf-8


from io import BytesIO

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, UploadFile
from fastapi.responses import Response, StreamingResponse
from loguru import logger
from pydantic import Field
from typing_extensions import Annotated

from src.services import RESOURCE_TYPE, db, embd_extractor, embd_store, keyword_extractor, obj_store

router = APIRouter(
    prefix="/resource",
    tags=["Resource"],
)


def process_uploaded_file(raw: bytes, filename: str, content_type: str, thres_match: float = 0.95):
    # =================================================
    # Extract stuffs related to resource
    # =================================================
    # Extract keywords
    logger.debug("Extract keywords")

    keywords = keyword_extractor.extract_keyword(raw)

    # Extract embedding
    logger.debug("Extract embeddings")

    embd_keywords = embd_extractor.get_embd_text([word["word"] for word in keywords if word is not None])
    embd_img = embd_extractor.get_embd_image(BytesIO(raw))

    # =================================================
    # Check matching
    # =================================================
    # Check match using image
    logger.debug("Check matching with image")

    out = embd_store.search_similar_res(embd_img)
    if out != []:
        res_similar = out[0]
        if res_similar.similarity >= thres_match:
            logger.info(f"Uploaded resource similar with one already in system: {res_similar.resource_id}")
            return

    keywords_similar = embd_store.search_similar_keyword(embd_keywords)
    for similar, keyword in zip(keywords_similar, keywords):
        keyword["resource_id"] = (
            similar[0].resource_id if similar != [] and similar[0].similarity >= thres_match else None
        )

    # =================================================
    # Store extracted things
    # =================================================

    # Store in Object store
    logger.debug("Store file")

    obj_store.save(filename, BytesIO(raw))

    # Store new keywords in Attribute DB and Embd store
    logger.debug("Store keyword")

    for keyword, embd in zip(keywords, embd_keywords):
        if keyword["resource_id"] is not None:
            continue

        instance = db.insert_keyword(keyword["category"], keyword["word"])
        keyword["resource_id"] = instance.id

        embd_store.insert_keyword_embd(embd, instance.id)

    # Store resource metadata in Attribute DB
    logger.debug("Store metadata")

    assert content_type
    logger.debug(f"content_type: {content_type}")
    if content_type.startswith("image"):
        res_type = RESOURCE_TYPE.IMAGE.val
    elif content_type.startswith("video"):
        res_type = RESOURCE_TYPE.VIDEO.val
    else:
        raise NotImplementedError()
    resource = db.insert_resource(res_type, filename, [word["word"] for word in keywords])

    # Store in Embedding store
    logger.debug("Store embedding")

    assert resource.id
    embd_store.insert_res_embd(embd_img, resource.id)


@router.post(
    "",
    responses={
        202: {"model": object, "description": "Accepted"},
        422: {"model": object, "description": "Validation Error"},
    },
    summary="Upload item",
    response_model_by_alias=True,
)
async def resource_post(file: UploadFile, background_tasks: BackgroundTasks) -> object:
    raw = await file.read()
    assert file.filename and file.content_type
    background_tasks.add_task(process_uploaded_file, raw, file.filename, file.content_type)

    return Response(status_code=202, content="Uploaded file is queued for processing")


@router.get(
    "/{resourceId}",
    responses={
        200: {"model": object, "description": "Successful Response"},
        422: {"model": object, "description": "Validation Error"},
        404: {"model": object, "description": "Resource not found"},
    },
    summary="Get resource via ID",
    response_model=None,
)
async def resource_resource_id_get(
    resource_id: Annotated[int, Field(description="Resource ID")] = Path(..., description="Resource ID", ge=0),
) -> StreamingResponse:
    # TODO: HoangLe [Jul-20]: Implement this
    resource = db.fetch_resource(resource_id=resource_id)

    if resource is None:
        raise HTTPException(404, "Resource not found")

    data = obj_store.load(resource.name)
    match resource.res_type.type:
        case RESOURCE_TYPE.IMAGE.val:
            media_type = "image/png"
        case RESOURCE_TYPE.VIDEO.val:
            media_type = "video/mp4"
        case _:
            raise NotImplementedError()

    return StreamingResponse(BytesIO(data), media_type=media_type)
