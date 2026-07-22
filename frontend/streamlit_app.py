import os
from pathlib import Path
from urllib.parse import quote

import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
SAMPLE_DOCS_DIR = Path("data/sample_docs")

SAMPLE_DOCUMENTS = [
  ("🏥", "Healthcare Handbook", "healthcare_handbook.txt", "Hospital policies and HIPAA rules", "#0EA5E9"),
  ("👥", "HR Employee Handbook", "hr_employee_handbook.txt", "PTO, remote work, and benefits", "#8B5CF6"),
  ("🔐", "IT Security Policy", "it_security_policy.txt", "Passwords, VPN, and security", "#F59E0B"),
  ("💳", "Finance Expense Policy", "finance_expense_policy.txt", "Travel limits and expense rules", "#10B981"),
]

DOC_COLORS = ["#6366F1", "#0EA5E9", "#8B5CF6", "#F59E0B", "#10B981", "#EC4899"]

CUSTOM_CSS = """
<style>
/* ---------- Colorful page background with visible gradient blobs ---------- */
.stApp {
  background:
    radial-gradient(600px 400px at 0% 0%, rgba(99, 102, 241, 0.18), transparent 60%),
    radial-gradient(700px 500px at 100% 0%, rgba(236, 72, 153, 0.14), transparent 60%),
    radial-gradient(700px 500px at 20% 100%, rgba(14, 165, 233, 0.16), transparent 60%),
    radial-gradient(600px 400px at 90% 90%, rgba(16, 185, 129, 0.12), transparent 60%),
    linear-gradient(180deg, #F6F7FF 0%, #FDF7FF 50%, #F4FBFF 100%);
  background-attachment: fixed;
}
.block-container {
  padding-top: 1rem;
  padding-bottom: 2rem;
  max-width: 1360px;
}

/* Hide Streamlit toolbar (Deploy button etc.) */
[data-testid="stToolbar"] { display: none; }

/* ---------- Hero banner with decorative circles ---------- */
.hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(120deg, #4F46E5 0%, #7C3AED 45%, #DB2777 100%);
  border-radius: 18px;
  padding: 1.9rem 2.2rem;
  margin-bottom: 1.3rem;
  color: #FFFFFF;
  box-shadow: 0 16px 40px rgba(109, 40, 217, 0.35);
}
.hero::before, .hero::after {
  content: "";
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
}
.hero::before {
  width: 260px; height: 260px;
  top: -120px; right: -60px;
  border: 30px solid rgba(255, 255, 255, 0.08);
}
.hero::after {
  width: 160px; height: 160px;
  bottom: -80px; left: 22%;
  border: 22px solid rgba(255, 255, 255, 0.08);
}
.hero h1 {
  font-size: 1.8rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 0 0 0.35rem 0;
  color: #FFFFFF;
  position: relative; z-index: 1;
}
.hero p {
  margin: 0;
  font-size: 0.96rem;
  opacity: 0.95;
  max-width: 50rem;
  position: relative; z-index: 1;
  line-height: 1.45;
}

/* How-it-works strip under the hero */
.how-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin: 0 0 1.2rem 0;
}
.how-card {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid #E6E8F0;
  border-radius: 12px;
  padding: 0.85rem 0.95rem;
  box-shadow: 0 4px 12px rgba(80, 70, 230, 0.06);
}
.how-card .step {
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #7C3AED;
  margin-bottom: 0.25rem;
}
.how-card .title {
  font-size: 0.9rem;
  font-weight: 700;
  color: #1E1B4B;
  margin-bottom: 0.2rem;
}
.how-card .desc {
  font-size: 0.78rem;
  color: #667085;
  line-height: 1.35;
}
@media (max-width: 900px) {
  .how-strip { grid-template-columns: 1fr 1fr; }
}

/* Status pills */
.pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.85rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  margin-right: 0.45rem;
  margin-top: 0.8rem;
  position: relative; z-index: 1;
}
.pill-glass { background: rgba(255,255,255,0.2); color: #FFFFFF; border: 1px solid rgba(255,255,255,0.35); }
.pill-warn  { background: #FEF3C7; color: #92400E; }
.pill-err   { background: #FEE2E2; color: #991B1B; }

/* ---------- Gradient section titles ---------- */
.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.02rem;
  font-weight: 800;
  color: #1E1B4B;
  margin: 0 0 0.7rem 0;
}
.section-title .bar {
  width: 6px;
  height: 20px;
  border-radius: 4px;
}
.bar-indigo { background: linear-gradient(180deg, #6366F1, #A855F7); }
.bar-pink   { background: linear-gradient(180deg, #EC4899, #F97316); }
.bar-sky    { background: linear-gradient(180deg, #0EA5E9, #22D3EE); }

/* ---------- Cards (main area only, never the sidebar) ---------- */
div[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(226, 229, 240, 0.9) !important;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(80, 70, 230, 0.08);
}

/* Make the Knowledge Query card fill the page height */
div[data-testid="stMain"] div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stVerticalBlockBorderWrapper"] {
  min-height: 620px;
}

/* ---------- Document rows (color-coded) ---------- */
.doc-row {
  border-radius: 11px;
  padding: 0.6rem 0.9rem;
  margin-bottom: 0.5rem;
  background: #FFFFFF;
  border: 1px solid #ECEEF6;
  box-shadow: 0 2px 6px rgba(16, 24, 40, 0.05);
}
.doc-row .name { font-size: 0.86rem; font-weight: 700; color: #1E1B4B; }
.doc-row .meta { font-size: 0.75rem; color: #6B7280; margin-top: 1px; }

.empty-state {
  border: 2px dashed #C7CBF4;
  border-radius: 12px;
  padding: 1rem;
  margin: 0.25rem 0.35rem 1rem 0.35rem;
  text-align: center;
  color: #6B7280;
  font-size: 0.85rem;
  background: linear-gradient(180deg, #FBFBFF, #F6F7FF);
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #1E1B4B 0%, #312E81 60%, #4C1D95 100%);
}

/* Keep every inner sidebar wrapper transparent so the gradient shows through */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"],
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"],
section[data-testid="stSidebar"] div[data-testid="stSidebarContent"],
section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

/* Sidebar text always light */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  color: #DDE3FF !important;
}

section[data-testid="stSidebar"] .stButton button,
section[data-testid="stSidebar"] .stDownloadButton button {
  border-radius: 10px;
  border: 1px solid rgba(224, 231, 255, 0.35);
  background: rgba(255, 255, 255, 0.12) !important;
  font-weight: 700;
  text-align: left;
  transition: all 0.15s ease;
}
section[data-testid="stSidebar"] .stButton button p,
section[data-testid="stSidebar"] .stButton button span,
section[data-testid="stSidebar"] .stDownloadButton button p,
section[data-testid="stSidebar"] .stDownloadButton button span {
  color: #FFFFFF !important;
}
section[data-testid="stSidebar"] .stButton button:hover,
section[data-testid="stSidebar"] .stDownloadButton button:hover {
  background: rgba(255, 255, 255, 0.22) !important;
  border-color: rgba(255, 255, 255, 0.6);
  transform: translateY(-1px);
}
section[data-testid="stSidebar"] hr { border-color: rgba(224, 231, 255, 0.25); }

.side-label {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #A5B4FC;
  margin-bottom: 0.4rem;
}

/* ---------- Main buttons: gradient ---------- */
div[data-testid="stMain"] .stButton button {
  border-radius: 10px;
  font-weight: 700;
  border: 1px solid #E3E6F2;
}
div[data-testid="stMain"] .stButton button[kind="primary"] {
  background: linear-gradient(90deg, #6366F1, #A855F7);
  border: none;
  color: white;
}
div[data-testid="stMain"] .stButton button[kind="primary"]:hover {
  box-shadow: 0 6px 16px rgba(124, 58, 237, 0.4);
}

/* ---------- Chat ---------- */
[data-testid="stChatMessage"] {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #ECEEF6;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(16, 24, 40, 0.05);
  margin-bottom: 0.5rem;
}

/* File uploader dropzone */
[data-testid="stFileUploaderDropzone"] {
  border-radius: 12px;
  border: 2px dashed #C7CBF4;
  background: linear-gradient(180deg, #FBFBFF, #F4F5FF);
}

/* Hide default chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
</style>
"""


def _error_message(response: httpx.Response) -> str:
  try:
    payload = response.json()
    if isinstance(payload, dict):
      return str(payload.get("detail", payload))
  except Exception:
    pass
  return response.text or f"Request failed with status {response.status_code}"


def _upload_file(filename: str, content: bytes) -> tuple[bool, str]:
  response = httpx.post(
    f"{API_URL}/upload",
    files={"file": (filename, content)},
    timeout=120.0,
  )
  if response.status_code == 200:
    data = response.json()
    return True, data["filename"]
  return False, _error_message(response)


def _ask_question(
  question: str,
  document: str,
) -> tuple[bool, dict | str]:
  response = httpx.post(
    f"{API_URL}/ask",
    json={"question": question, "document": document},
    timeout=120.0,
  )
  if response.status_code != 200:
    return False, _error_message(response)
  return True, response.json()


def _delete_document(filename: str) -> tuple[bool, str]:
  encoded_filename = quote(filename, safe="")
  response = httpx.delete(
    f"{API_URL}/documents/{encoded_filename}",
    timeout=30.0,
  )
  if response.status_code == 200:
    return True, response.json().get("message", "Document removed.")
  return False, _error_message(response)


st.set_page_config(
  page_title="Enterprise RAG Assistant",
  page_icon="📄",
  layout="wide",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "uploaded_files" not in st.session_state:
  st.session_state.uploaded_files = set()
if "messages" not in st.session_state:
  st.session_state.messages = []
if "upload_notice" not in st.session_state:
  st.session_state.upload_notice = None
if "upload_error" not in st.session_state:
  st.session_state.upload_error = None


def _mark_upload_success(filename: str, file_key: str) -> None:
  st.session_state.uploaded_files.add(file_key)
  st.session_state.upload_notice = f"**{filename}** has been added to the knowledge base."
  st.session_state.upload_error = None


# --- Health check ---
api_online = False
llm_ready = False
llm_provider = ""
chunk_count = 0
try:
  health = httpx.get(f"{API_URL}/health", timeout=5.0).json()
  api_online = True
  chunk_count = health.get("documents_indexed", 0)
  llm_ready = bool(health.get("llm_ready"))
  llm_provider = str(health.get("llm_provider", "gemini")).title()
except Exception:
  pass

# --- Hero banner ---
if api_online and llm_ready:
  pills = (
    '<span class="pill pill-glass">🟢 Service online</span>'
    f'<span class="pill pill-glass">✨ {llm_provider} connected</span>'
    f'<span class="pill pill-glass">🗂 {chunk_count} indexed sections</span>'
  )
elif api_online:
  pills = (
    '<span class="pill pill-glass">🟢 Service online</span>'
    '<span class="pill pill-warn">⚠ Model not configured</span>'
    f'<span class="pill pill-glass">🗂 {chunk_count} indexed sections</span>'
  )
else:
  pills = (
    '<span class="pill pill-err">🔴 Backend API offline</span>'
    '<span class="pill pill-warn">Service is starting or unavailable</span>'
  )

st.markdown(
  f"""
  <div class="hero">
    <h1>📄 Enterprise RAG Knowledge Assistant</h1>
    <p>
      An enterprise knowledge assistant built with <b>Retrieval-Augmented Generation (RAG)</b>.
      Upload policy handbooks and operational documents, submit document-specific queries,
      and receive responses synthesized from semantically retrieved passages with file and page citations.
    </p>
    {pills}
  </div>
  <div class="how-strip">
    <div class="how-card">
      <div class="step">Step 1</div>
      <div class="title">Upload or load a document</div>
      <div class="desc">Add PDF, TXT, or DOCX files, or load a sample from the sidebar.</div>
    </div>
    <div class="how-card">
      <div class="step">Step 2</div>
      <div class="title">Index into the knowledge base</div>
      <div class="desc">Text is chunked and embedded so relevant sections can be retrieved.</div>
    </div>
    <div class="how-card">
      <div class="step">Step 3</div>
      <div class="title">Ask a question</div>
      <div class="desc">Vector similarity search retrieves relevant chunks for response generation.</div>
    </div>
    <div class="how-card">
      <div class="step">Step 4</div>
      <div class="title">Review source citations</div>
      <div class="desc">Open reference sources under each answer to verify the evidence.</div>
    </div>
  </div>
  """,
  unsafe_allow_html=True,
)

# --- Sidebar ---
with st.sidebar:
  st.markdown('<div class="side-label">📚 Sample documents</div>', unsafe_allow_html=True)
  st.caption("Load a sample into the knowledge base, or download a copy for manual upload.")

  for icon, domain, filename, description, _color in SAMPLE_DOCUMENTS:
    path = SAMPLE_DOCS_DIR / filename
    st.caption(description)
    col_load, col_dl = st.columns([3, 1])
    with col_load:
      if st.button(f"{icon}  {domain}", use_container_width=True, key=f"load_{filename}"):
        file_key = f"{filename}:{path.stat().st_size}"
        with st.spinner(f"Indexing {filename}..."):
          ok, result = _upload_file(filename, path.read_bytes())
        if ok:
          _mark_upload_success(result, file_key)
          st.rerun()
        else:
          st.session_state.upload_error = result
          st.rerun()
    with col_dl:
      st.download_button(
        "⬇",
        data=path.read_bytes(),
        file_name=filename,
        mime="text/plain",
        key=f"dl_{filename}",
        help=f"Download {filename}",
        use_container_width=True,
      )

  st.divider()
  st.markdown('<div class="side-label">Supported formats</div>', unsafe_allow_html=True)
  st.caption("PDF · TXT · DOCX")

  st.divider()
  st.markdown('<div class="side-label">About this project</div>', unsafe_allow_html=True)
  st.caption(
    "This assistant uses FastAPI, LangChain, ChromaDB, FastEmbed, and Google Gemini "
    "to answer questions from uploaded enterprise documents across domains such as "
    "healthcare, HR, IT security, and finance."
  )

# --- Main layout ---
col_left, col_right = st.columns([1, 2], gap="medium")

with col_left:
  with st.container(border=True):
    st.markdown(
      '<div class="section-title"><span class="bar bar-pink"></span>📤 Document Upload</div>',
      unsafe_allow_html=True,
    )

    if st.session_state.upload_notice:
      st.success(st.session_state.upload_notice)

    if st.session_state.upload_error:
      st.error(f"Upload failed: {st.session_state.upload_error}")

    uploaded = st.file_uploader(
      "Select document", type=["pdf", "txt", "docx"], label_visibility="collapsed"
    )

    if uploaded is not None:
      file_key = f"{uploaded.name}:{uploaded.size}"

      if file_key not in st.session_state.uploaded_files:
        with st.spinner("Processing document..."):
          ok, result = _upload_file(uploaded.name, uploaded.getvalue())
        if ok:
          _mark_upload_success(result, file_key)
          st.rerun()
        else:
          st.session_state.upload_error = result
          st.session_state.upload_notice = None
          st.rerun()

  with st.container(border=True):
    st.markdown(
      '<div class="section-title"><span class="bar bar-sky"></span>🗂️ Document Library</div>',
      unsafe_allow_html=True,
    )

    docs = []
    try:
      docs = httpx.get(f"{API_URL}/documents", timeout=30.0).json()
      if docs:
        for idx, doc in enumerate(docs):
          color = DOC_COLORS[idx % len(DOC_COLORS)]
          col_doc, col_delete = st.columns([8, 1], vertical_alignment="center")
          with col_doc:
            st.markdown(
              f"""
              <div class="doc-row" style="border-left: 5px solid {color};">
                <div class="name">📄 {doc["filename"]}</div>
                <div class="meta">{doc["chunks"]} searchable sections</div>
              </div>
              """,
              unsafe_allow_html=True,
            )
          with col_delete:
            if st.button(
              "✕",
              key=f"delete_{doc['filename']}",
              help=f"Remove {doc['filename']}",
              use_container_width=True,
            ):
              ok, message = _delete_document(doc["filename"])
              if ok:
                st.session_state.upload_notice = message
                st.session_state.upload_error = None
                if st.session_state.get("selected_document") == doc["filename"]:
                  st.session_state.pop("selected_document", None)
              else:
                st.session_state.upload_error = message
              st.rerun()

        filenames = [doc["filename"] for doc in docs]
        if st.session_state.get("selected_document") not in filenames:
          st.session_state.selected_document = filenames[0]

        st.divider()
        st.selectbox(
          "Document to use for questions",
          options=filenames,
          key="selected_document",
          help="Only this document will be searched when you ask a question.",
        )
      else:
        st.session_state.pop("selected_document", None)
        st.markdown(
          '<div class="empty-state">🗃️ No documents indexed yet.<br>'
          "Load a sample from the sidebar or upload a file.</div>",
          unsafe_allow_html=True,
        )
    except Exception:
      st.caption("Unable to load document library.")

with col_right:
  with st.container(border=True):
    col_title, col_clear_chat = st.columns([4, 1], vertical_alignment="center")
    with col_title:
      st.markdown(
        '<div class="section-title"><span class="bar bar-indigo"></span>💬 Knowledge Query</div>',
        unsafe_allow_html=True,
      )
    with col_clear_chat:
      if st.button(
        "🗑 Clear chat",
        use_container_width=True,
        disabled=not st.session_state.messages,
      ):
        st.session_state.messages = []
        st.rerun()

    if chunk_count == 0:
      st.info("Index a document to begin. Load a sample from the sidebar or upload a file.")
    elif st.session_state.get("selected_document"):
      st.info(
        f"Questions currently use: **{st.session_state.selected_document}**"
      )

    for message in st.session_state.messages:
      avatar = "🧑‍💼" if message["role"] == "user" else "🤖"
      with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message.get("sources"):
          with st.expander(f"📎 Reference sources ({len(message['sources'])})"):
            for i, source in enumerate(message["sources"], start=1):
              page = (
                f" · Page {source['page'] + 1}"
                if source.get("page") is not None
                else ""
              )
              st.markdown(f"**[{i}] {source['source']}**{page}")
              excerpt = source["content"]
              if len(excerpt) > 600:
                excerpt = excerpt[:600] + "..."
              st.write(excerpt)
              if i < len(message["sources"]):
                st.divider()

    question = st.chat_input(
      "Ask a question about your documents...",
      disabled=not st.session_state.get("selected_document"),
    )

    if question:
      st.session_state.messages.append({"role": "user", "content": question})

      with st.spinner("Retrieving context and generating response..."):
        ok, result = _ask_question(
          question.strip(),
          st.session_state.selected_document,
        )

      if not ok:
        st.session_state.messages.append(
          {"role": "assistant", "content": f"**Error:** {result}"}
        )
      else:
        data = result
        status = ""
        if data["used_llm"]:
          provider = data.get("llm_provider", "gemini").title()
          status = (
            f"✨ *Response generated by {provider} "
            "from retrieved document context.*\n\n"
          )
        else:
          status = (
            "📄 *Language model unavailable — showing the most relevant "
            "passages from your documents.*\n\n"
          )
        st.session_state.messages.append(
          {
            "role": "assistant",
            "content": status + data["answer"],
            "sources": data.get("sources", []),
          }
        )

      st.rerun()
