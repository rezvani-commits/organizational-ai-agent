import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    AVALAI_API_KEY = os.getenv("AVALAI_API_KEY")

    main_Model_Api_key = AVALAI_API_KEY
    response_validator_api_key = AVALAI_API_KEY

    AVALAI_BASE_URL = "https://api.avalai.ir/v1"

    LLM_MODEL =  "gpt-4.1-mini"
    VALIDATOR_LLM_MODEL = "gemini-2.5-flash"
    ROUTER_LLM_MODEL = "gpt-4.1-mini"


    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

    TEMPERATURE = 0.3
    MAX_TOKENS = 4096
    TOP_P = 0.95

    ROUTER_TEMPERATURE = 0.0

    TOP_K = 5
    MAX_RETRIES = 2
    TOP_K_INCREMENT = 2

    CHROMA_PATH = os.getenv("CHROMA_PATH", "chromaStore")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "legal_docs")
    NORMALIZED_DATA_PATH = os.getenv("NORMALIZED_DATA_PATH", "dataNormalized/dataset_normalized.json")
    REGISTRY_PATH = os.getenv("REGISTRY_PATH", "data/documents_registry.json")

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")

    if all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        DB_URL = (
            f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    else:
        DB_URL = os.getenv("DATABASE_URL")

    DB_POOL_SIZE = 5
    DB_MAX_OVERFLOW = 10
    CHAT_HISTORY_DB_URL = DB_URL

    MAX_HISTORY_TURNS = 6
    CHAT_HISTORY_TABLE_NAME = "message_store"
    CHAT_HISTORY_POOL_SIZE = 5
    CHAT_HISTORY_MAX_OVERFLOW = 10

    _DB_USER = os.getenv("DB_USER")
    _DB_PASSWORD = os.getenv("DB_PASSWORD")
    _DB_HOST = os.getenv("DB_HOST")
    _DB_PORT = os.getenv("DB_PORT")
    _DB_NAME = os.getenv("DB_NAME")

    if all([_DB_USER, _DB_PASSWORD, _DB_HOST, _DB_PORT, _DB_NAME]):
        CHAT_HISTORY_DB_URL = (
            f"postgresql+psycopg2://{_DB_USER}:{_DB_PASSWORD}"
            f"@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"
        )
    else:
        CHAT_HISTORY_DB_URL = os.getenv("CHAT_HISTORY_DB_URL", "sqlite:///chat_history.db")

    FAITHFULNESS_THRESHOLD = 7.0
    RELEVANCE_THRESHOLD = 7.0
    COMPLETENESS_THRESHOLD = 6.0

    NOT_FOUND_PHRASE = "این اطلاعات در اسناد قابل‌دسترسی شما یافت نشد. در صورت نیاز، درخواست ارتقای سطح دسترسی را با مدیر خود مطرح کنید"

    MAX_SUB_QUESTIONS = 5
    INLINE_SUMMARY_MIN_CHARS = 250

    @classmethod
    def validate(cls):
        if not cls.mainApiModel:
            raise ValueError("❌ AVALAI_API_KEY  Model not found in .env file!")
        return True