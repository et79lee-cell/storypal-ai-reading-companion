from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("STORYPAL_HOST", "127.0.0.1")
    port: int = int(os.getenv("STORYPAL_PORT", "8000"))
    demo_mode: bool = os.getenv("STORYPAL_DEMO_MODE", "true").lower() == "true"


settings = Settings()
