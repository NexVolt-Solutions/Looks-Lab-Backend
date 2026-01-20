from pydantic_settings import BaseSettings

class HaircareAIConfig(BaseSettings):
    MIN_ANSWERS_REQUIRED: int = 4
    REQUIRE_IMAGES: bool = False

config = HaircareAIConfig()

