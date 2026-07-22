import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _is_placeholder(value: str, placeholders: tuple[str, ...]) -> bool:
  cleaned = value.strip().lower()
  if not cleaned:
    return True
  return any(p in cleaned for p in placeholders)


def _resolve_gemini_api_key() -> str | None:
  key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")).strip()
  if _is_placeholder(key, ("your-key", "paste", "here", "example")):
    return None
  return key


class Settings:
  llm_provider: str = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
  gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
  embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
  chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
  upload_dir: str = os.getenv("UPLOAD_DIR", "./data/uploads")
  chunk_size: int = int(os.getenv("CHUNK_SIZE", "800"))
  chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))
  top_k: int = int(os.getenv("TOP_K", "4"))

  @property
  def gemini_api_key(self) -> str | None:
    return _resolve_gemini_api_key()

  @property
  def llm_ready(self) -> bool:
    return self.llm_provider != "none" and self.gemini_api_key is not None


settings = Settings()

Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
