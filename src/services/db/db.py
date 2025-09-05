from datetime import datetime

from sqlmodel import Session, SQLModel, col, create_engine, select

from src import config

from .model import Keyword, KeywordCategory, Resource, ResourceType

db_url = f"postgresql+psycopg://{config.DB_USER}:{config.DB_PWD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
engine = create_engine(db_url)
session = Session(engine)


def create_db():
    SQLModel.metadata.create_all(engine)


def _fetch_resource_type(resource_type: str) -> ResourceType:
    stmt = select(ResourceType).where(ResourceType.type == resource_type)

    result = session.exec(stmt).first()

    assert result is not None

    return result


def _fetch_keyword(keywords: str | list[str]) -> list[Keyword]:
    if isinstance(keywords, str):
        keywords = [keywords]
    stmt = select(Keyword).where(col(Keyword.word).in_(keywords))

    result = list(session.exec(stmt).all())

    return result


def _fetch_keyword_cat(category: str) -> KeywordCategory:
    stmt = select(KeywordCategory).where(KeywordCategory.category_name == category)

    out = session.exec(stmt).first()
    assert out is not None

    return out


# =================================================
# Insert
# =================================================


def insert_keyword(category: str, word: str, embd_id: int):
    kw_cat_instance = _fetch_keyword_cat(category)

    keyword = Keyword(word=word, embd_id=embd_id, category=kw_cat_instance)
    session.add(keyword)
    session.commit()


def insert_resource(resource_type: str, name: str, embd_id: int, keywords: list[str]):
    # Convert 'resource' to 'resource_type' in id
    resource_type_instance = _fetch_resource_type(resource_type)

    # Convert keywords to list of ids of corresponding keywords
    keyword_instances = _fetch_keyword(keywords)

    resource = Resource(
        name=name,
        date_added=datetime.now(),
        embd_id=embd_id,
        keywords=[keyword.id for keyword in keyword_instances],
        res_type=resource_type_instance,
    )
    session.add(resource)
    session.commit()


def insert_resource_type(resource_type: str):
    session.add(ResourceType(type=resource_type))
    session.commit()


def insert_keyword_cat(category: str):
    session.add(KeywordCategory(category_name=category))
    session.commit()
