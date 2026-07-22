from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
  status: str
  documents_indexed: int
  llm_provider: str
  llm_ready: bool


class UploadResponse(BaseModel):
  filename: str
  chunks_added: int
  message: str


class AskRequest(BaseModel):
  question: str = Field(..., min_length=3)
  document: str | None = None


class SourceChunk(BaseModel):
  content: str
  source: str
  page: int | None = None


class AskResponse(BaseModel):
  answer: str
  sources: list[SourceChunk]
  used_llm: bool
  llm_provider: str


class DocumentInfo(BaseModel):
  filename: str
  chunks: int


class DocumentDeleteResponse(BaseModel):
  filename: str
  chunks_removed: int
  message: str
