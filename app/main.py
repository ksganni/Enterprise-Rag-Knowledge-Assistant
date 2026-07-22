import shutil
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.schemas import (
  AskRequest,
  AskResponse,
  DocumentDeleteResponse,
  DocumentInfo,
  HealthResponse,
  SourceChunk,
  UploadResponse,
)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

app = FastAPI(
  title="Enterprise RAG Knowledge Assistant",
  description="Upload documents and ask questions using RAG.",
  version="1.0.0",
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
  return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
  documents_indexed = 0
  try:
    from app.rag.vectorstore import count_indexed_chunks

    documents_indexed = count_indexed_chunks()
  except Exception:
    documents_indexed = 0

  return HealthResponse(
    status="ok",
    documents_indexed=documents_indexed,
    llm_provider=settings.llm_provider,
    llm_ready=settings.llm_ready,
  )


@app.get("/documents", response_model=list[DocumentInfo])
def documents() -> list[DocumentInfo]:
  from app.rag.vectorstore import list_documents

  return [
    DocumentInfo(filename=name, chunks=count)
    for name, count in sorted(list_documents().items())
  ]


@app.delete("/documents/{filename}", response_model=DocumentDeleteResponse)
def remove_document(filename: str) -> DocumentDeleteResponse:
  from app.rag.vectorstore import delete_document

  if Path(filename).name != filename:
    raise HTTPException(status_code=400, detail="Invalid filename.")

  removed = delete_document(filename)
  if removed == 0:
    raise HTTPException(status_code=404, detail="Document not found.")

  (Path(settings.upload_dir) / filename).unlink(missing_ok=True)

  return DocumentDeleteResponse(
    filename=filename,
    chunks_removed=removed,
    message=f"{filename} removed from the document library.",
  )


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
  from app.rag.ingest import load_documents, split_documents
  from app.rag.vectorstore import add_documents, delete_document

  if not file.filename:
    raise HTTPException(status_code=400, detail="Filename is required.")

  safe_name = Path(file.filename).name
  if safe_name != file.filename or safe_name in {"", ".", ".."}:
    raise HTTPException(status_code=400, detail="Invalid filename.")

  suffix = Path(safe_name).suffix.lower()
  if suffix not in ALLOWED_EXTENSIONS:
    raise HTTPException(
      status_code=400,
      detail=f"Unsupported file type '{suffix}'. Use: pdf, txt, docx.",
    )

  dest = Path(settings.upload_dir) / safe_name
  with dest.open("wb") as buffer:
    shutil.copyfileobj(file.file, buffer)

  try:
    # Replace any previous index for this filename to avoid duplicate chunks.
    delete_document(safe_name)
    raw_docs = load_documents(dest)
    chunks = split_documents(raw_docs)
    added = add_documents(chunks)
  except Exception as exc:
    dest.unlink(missing_ok=True)
    raise HTTPException(status_code=400, detail=str(exc)) from exc

  return UploadResponse(
    filename=safe_name,
    chunks_added=added,
    message="Document processed and indexed successfully.",
  )


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
  from app.rag.chain import ask_question

  try:
    answer, docs, used_llm, llm_provider = ask_question(
      body.question,
      document=body.document,
    )
  except Exception as exc:
    # Retrieval itself failed (vector store / embeddings). LLM failures are
    # handled inside ask_question by returning document passages instead.
    raise HTTPException(
      status_code=502,
      detail=f"Retrieval error: {exc}",
    ) from exc

  sources = [
    SourceChunk(
      content=doc.page_content,
      source=doc.metadata.get("source", "unknown"),
      page=doc.metadata.get("page"),
    )
    for doc in docs
  ]

  return AskResponse(
    answer=answer,
    sources=sources,
    used_llm=used_llm,
    llm_provider=llm_provider,
  )
