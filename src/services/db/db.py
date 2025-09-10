from sqlmodel import Session, SQLModel, col, create_engine, select

from src import config

from .model import Keyword, KeywordCategory, Resource, ResourceType

db_url = f"postgresql+psycopg://{config.DB_USER}:{config.DB_PWD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
engine = create_engine(db_url)
session = Session(engine)


def create_db():
    SQLModel.metadata.create_all(engine)


# =================================================
# Fetch
# =================================================


def fetch_resource_type(resource_type: str) -> ResourceType:
    stmt = select(ResourceType).where(ResourceType.type == resource_type)

    result = session.exec(stmt).first()

    assert result is not None

    return result


def fetch_keyword(keywords: str | list[str]) -> list[Keyword]:
    if isinstance(keywords, str):
        keywords = [keywords]
    stmt = select(Keyword).where(col(Keyword.word).in_(keywords))

    result = list(session.exec(stmt).all())

    return result


def fetch_keyword_cat(category: str) -> KeywordCategory:
    stmt = select(KeywordCategory).where(KeywordCategory.category_name == category)

    out = session.exec(stmt).first()
    assert out is not None

    return out


def fetch_resource(resource_id: int) -> Resource | None:
    stmt = select(Resource).where(Resource.id == resource_id)

    out = session.exec(stmt).first()

    return out


# =================================================
# Insert
# =================================================


def insert_keyword(category: str, word: str) -> Keyword:
    kw_cat_instance = fetch_keyword_cat(category)

    keyword = Keyword(word=word, category=kw_cat_instance)
    session.add(keyword)
    session.commit()
    session.refresh(keyword)

    return keyword


def insert_resource(resource_type: str, name: str, keywords: list[str]) -> Resource:
    # Convert 'resource' to 'resource_type' in id
    resource_type_instance = fetch_resource_type(resource_type)

    # Convert keywords to list of ids of corresponding keywords
    keyword_instances = fetch_keyword(keywords)

    resource = Resource(
        name=name,
        keywords=[keyword.id for keyword in keyword_instances],
        res_type=resource_type_instance,
    )
    session.add(resource)
    session.commit()
    session.refresh(resource)

    return resource


def insert_resource_type(resource_type: str):
    session.add(ResourceType(type=resource_type))
    session.commit()


def insert_keyword_cat(category: str):
    session.add(KeywordCategory(category_name=category))
    session.commit()
