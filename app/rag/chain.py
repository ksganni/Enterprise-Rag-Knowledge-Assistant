from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.rag.vectorstore import search_documents

SYSTEM_PROMPT = """You are a helpful enterprise knowledge assistant.
Answer ONLY using the provided context from uploaded documents.
If the answer is not in the context, say you do not have enough information.
Keep answers clear, concise, and professional."""

# Prefer models with higher free-tier RPM. gemini-3.5-flash is capped low
# and causes long LangChain retry delays when that quota is hit.
GEMINI_FALLBACK_MODELS = (
  "gemini-2.5-flash",
  "gemini-flash-latest",
  "gemini-2.0-flash",
  "gemini-2.5-flash-lite",
)

# Fail over to retrieved passages instead of hanging on a slow Gemini call.
GEMINI_TIMEOUT_SECONDS = 20


def _format_context(docs: list[Document]) -> str:
  parts = []
  for i, doc in enumerate(docs, start=1):
    source = doc.metadata.get("source", "unknown")
    page = doc.metadata.get("page")
    page_info = f", page {page + 1}" if page is not None else ""
    parts.append(f"[{i}] Source: {source}{page_info}\n{doc.page_content}")
  return "\n\n".join(parts)


def _source_label(doc: Document) -> str:
  source = doc.metadata.get("source", "unknown")
  page = doc.metadata.get("page")
  if page is not None:
    return f"{source}, page {page + 1}"
  return str(source)


def _snippet_answer(docs: list[Document], note: str) -> str:
  if not docs:
    return "No documents are in the knowledge base. Upload a PDF, TXT, or DOCX file first."

  parts = []
  for i, doc in enumerate(docs, start=1):
    text = doc.page_content.strip()
    if len(text) > 800:
      text = text[:800] + "..."
    parts.append(f"**[{i}] {_source_label(doc)}**\n\n{text}")

  return f"{note}\n\n" + "\n\n---\n\n".join(parts)


def _retrieval_fallback(
  docs: list[Document],
  reason: str,
) -> tuple[str, list[Document], bool, str]:
  return (
    _snippet_answer(
      docs,
      f"{reason} Showing the most relevant passages from your documents:",
    ),
    docs,
    False,
    "gemini",
  )


def _is_quota_error(exc: Exception) -> bool:
  message = str(exc).lower()
  return any(
    token in message
    for token in ("429", "quota", "rate limit", "resource_exhausted")
  )


def _is_model_not_found(exc: Exception) -> bool:
  message = str(exc).lower()
  return "not found" in message and "model" in message


def _is_transient_llm_error(exc: Exception) -> bool:
  message = str(exc).lower()
  return any(
    token in message
    for token in (
      "timeout",
      "timed out",
      "deadline",
      "unavailable",
      "connection",
      "temporarily",
      "503",
      "500",
      "502",
      "504",
    )
  )


def _gemini_models_to_try() -> list[str]:
  models: list[str] = []
  for name in (settings.gemini_model, *GEMINI_FALLBACK_MODELS):
    if name and name not in models:
      models.append(name)
  return models


def _invoke_gemini(question: str, context: str) -> str:
  messages = [
    ("system", SYSTEM_PROMPT),
    ("human", f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"),
  ]

  last_error: Exception | None = None
  for model_name in _gemini_models_to_try():
    try:
      llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.gemini_api_key,
        temperature=0,
        max_retries=0,
        timeout=GEMINI_TIMEOUT_SECONDS,
      )
      response = llm.invoke(messages)
      return response.content
    except Exception as exc:
      last_error = exc
      # Fail over immediately instead of waiting on LangChain retry backoff.
      if (
        _is_quota_error(exc)
        or _is_model_not_found(exc)
        or _is_transient_llm_error(exc)
      ):
        continue
      raise

  raise last_error or RuntimeError("Gemini request failed")


def ask_question(
  question: str,
  document: str | None = None,
) -> tuple[str, list[Document], bool, str]:
  docs = search_documents(question, source=document)

  if settings.llm_provider == "none" or not settings.gemini_api_key:
    return (
      _snippet_answer(
        docs,
        "The following excerpts were retrieved from your uploaded documents:",
      ),
      docs,
      False,
      settings.llm_provider,
    )

  context = _format_context(docs)
  try:
    answer = _invoke_gemini(question, context)
    return answer, docs, True, "gemini"
  except Exception as exc:
    if _is_quota_error(exc):
      return _retrieval_fallback(
        docs,
        "The language model hit a rate limit.",
      )
    if _is_transient_llm_error(exc):
      return _retrieval_fallback(
        docs,
        "The language model is slow or temporarily unavailable.",
      )
    if _is_model_not_found(exc):
      return _retrieval_fallback(
        docs,
        "The configured language model is unavailable.",
      )
    # Any other LLM failure: still return retrieved pages instead of an error.
    return _retrieval_fallback(
      docs,
      "The language model could not generate an answer.",
    )
