from pydantic_settings import BaseSettings

class SkincareAIConfig(BaseSettings):
    MIN_ANSWERS_REQUIRED: int = 6
    REQUIRE_IMAGES: bool = True

config = SkincareAIConfig()

