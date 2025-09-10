import os

import torch
from dotenv import load_dotenv

load_dotenv()

# =================================================
# Configs for web server
# =================================================
FASTAPI_ENV = os.getenv("FASTAPI_ENV", "development")
API_VERSION = os.getenv("VERSION")

DB_PORT = os.getenv("DB_PORT")
DB_PWD = os.getenv("DB_PWD")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")


# =================================================
# Configs for Keyword Extractor
# =================================================
KEYWORD_MODEL_NAME = os.getenv("KEYWORD_MODEL_NAME")
PROMPTS_PATH = os.getenv("PROMPTS_PATH")


# =================================================
# Configs for Embedding Extractor
# =================================================
DEVICE = os.getenv("DEVICE", "cpu")
EMBD_MODEL_NAME = os.getenv("EMBD_MODEL_NAME", "openai/clip-vit-base-patch32")
EMBD_MODEL_PATH = os.getenv("EMBD_MODEL_PATH")
dtype = os.getenv("DTYPE", "float16")
match dtype:
    case "float32":
        DTYPE = torch.float32
    case "float16":
        DTYPE = torch.float16
    case _:
        raise NotImplementedError()


# =================================================
# Configs for embedding store
# =================================================
EMBDSTORE_HOST = os.getenv("EMBDSTORE_HOST")
EMBDSTORE_PORT = os.getenv("EMBDSTORE_PORT")


# =================================================
# Configs for object store
# =================================================
FILESTORE_DIR = os.getenv("FILESTORE_DIR")
