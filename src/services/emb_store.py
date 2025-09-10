import sys
from typing import List

from loguru import logger
from numpy import ndarray
from pydantic import BaseModel
from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

from src import config


class EmbdObj(BaseModel):
    obj_id: int
    similarity: float
    resource_id: int


class EmbdStoreController:
    def __init__(
        self,
        fieldname_id: str,
        fieldname_res_id: str,
        fieldname_embd: str,
        index_type: str,
        metric_type: str,
        coll_name: str,
        embd_dim: int,
    ):
        self.fieldname_id = fieldname_id
        self.fieldname_res_id = fieldname_res_id
        self.fieldname_embd = fieldname_embd
        self.index_type = index_type
        self.metric_type = metric_type
        self.coll_name = coll_name
        self.embd_dim = embd_dim

        self.collection = self._initialize()
        self.create_index()

    def _initialize(self) -> Collection:
        # Connect to embedding store
        try:
            connections.connect(host=config.EMBDSTORE_HOST, port=config.EMBDSTORE_PORT)
            logger.info("Connected to Milvus.")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus embedding store: {e}")

            sys.exit(1)

        # Create collection
        fields = [
            FieldSchema(name=self.fieldname_id, dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name=self.fieldname_res_id, dtype=DataType.INT64),
            FieldSchema(name=self.fieldname_embd, dtype=DataType.FLOAT16_VECTOR, dim=self.embd_dim),
        ]

        schema = CollectionSchema(fields)
        collection = Collection(self.coll_name, schema, consistency_level="Strong")
        return collection

    def drop_collection(self):
        utility.drop_collection(self.coll_name)
        logger.info(f"Dropped collection '{self.coll_name}'.")

    def insert(self, entities: list):
        self.collection.insert(entities)
        self.collection.flush()
        logger.info(f"Inserted data into '{self.coll_name}'")

    def create_index(self, nlist: int = 128):
        self.collection.create_index(
            self.fieldname_embd,
            {"index_type": self.index_type, "metric_type": self.metric_type, "params": {"nlist": nlist}},
        )

        logger.info(f"Index '{self.index_type}' created for field '{self.fieldname_embd}'.")

    def search(self, query: ndarray | List[ndarray], limit: int = 10, nprobe: int = 10) -> list[list[EmbdObj]]:
        if isinstance(query, ndarray):
            query = [query]

        self.collection.load()
        results = self.collection.search(
            query,
            self.fieldname_embd,
            {"metric_type": self.metric_type, "params": {"nprobe": nprobe}},
            limit=limit,
            output_fields=[self.fieldname_res_id],
        )

        output = []
        for result in results:
            arr = [
                EmbdObj(
                    obj_id=entry[self.fieldname_id],
                    similarity=entry["distance"],
                    resource_id=entry["entity"][self.fieldname_res_id],
                )
                for entry in result
            ]
            output.append(arr)

        return output


class EmbdStoreUtils:
    def __init__(
        self,
        index_type: str = "IVF_FLAT",
        metric_type: str = "COSINE",
        coll_name_res: str = "resource_embd",
        coll_name_keyword: str = "keyword_embd",
        embd_dim: int = 512,
    ):
        self.resource_embd = EmbdStoreController(
            fieldname_id="id",
            fieldname_res_id="resource_id",
            fieldname_embd="embd",
            index_type=index_type,
            metric_type=metric_type,
            coll_name=coll_name_res,
            embd_dim=embd_dim,
        )

        self.keyword_embd = EmbdStoreController(
            fieldname_id="id",
            fieldname_res_id="keyword_id",
            fieldname_embd="embd",
            index_type=index_type,
            metric_type=metric_type,
            coll_name=coll_name_keyword,
            embd_dim=embd_dim,
        )

    def insert_res_embd(self, embd: ndarray, res_id: int):
        entities = [[res_id], [embd]]
        self.resource_embd.insert(entities)

    def insert_keyword_embd(self, embd: ndarray | List[ndarray], keyword_id: int | List[int]):
        if isinstance(embd, ndarray):
            embd = [embd]
        if isinstance(keyword_id, int):
            keyword_id = [keyword_id]

        entities = [keyword_id, embd]
        self.keyword_embd.insert(entities)

    def search_similar_res(self, embd_res: ndarray, limit: int = 10) -> list[EmbdObj]:
        return self.resource_embd.search(embd_res, limit=limit)[0]

    def search_similar_keyword(self, embd_res: ndarray | list[ndarray], limit: int = 10) -> list[list[EmbdObj]]:
        return self.keyword_embd.search(embd_res, limit=limit)
