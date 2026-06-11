# pyre-ignore-all-errors
import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from src.ingestion import IngestionManager
from src.indexing import IndexingManager
from src.retrieval import RetrievalManager
from src.generation import GenerationManager
from src.wikipedia_service import WikipediaManager

load_dotenv()

st.set_page_config(page_title="Advanced Multi-Source RAG (Gemini)", layout="wide")

st.title("🚀 Advanced Multi-Source RAG System")
st.markdown("### Enterprise Knowledge Base powered by Gemini")

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    gemini_api_key = st.text_input(
        "Gemini API Key", type="password",
        value=os.getenv("GEMINI_API_KEY", "")
    )
    
    st.header("🔍 Search Options")
    enable_web_search = st.toggle("Enable Wikipedia Web Search", value=False)
    st.caption("When enabled, searches Wikipedia directly (ignores uploaded documents).")
    
    st.divider()
    st.header("📄 Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose PDF or CSV files",
        accept_multiple_files=True, type=["pdf", "csv"]
    )

    if st.button("🔧 Process & Index"):
        if not gemini_api_key:
            st.error("Please enter your Gemini API Key!")
        elif not uploaded_files:
            st.warning("Please upload at least one document.")
        else:
            with st.spinner("Processing documents and building indices…"):
                ingestion = IngestionManager()
                indexing = IndexingManager(gemini_api_key)
                
                all_pages = []
                for uploaded_file in uploaded_files:
                    suffix = os.path.splitext(uploaded_file.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_file.getbuffer())
                        tmp_path = tmp.name
                    
                    if uploaded_file.name.endswith(".pdf"):
                        pages = ingestion.load_pdf(tmp_path)
                    else:
                        pages = ingestion.load_csv(tmp_path)
                    all_pages.extend(pages)
                    os.unlink(tmp_path)
                
                if not all_pages:
                    st.warning("No content extracted from the uploaded files.")
                else:
                    chunks = ingestion.process_documents(all_pages)
                    st.info(f"Created {len(chunks)} chunks from {len(uploaded_files)} file(s).")
                    
                    vector_idx = indexing.create_vector_index(chunks)
                    sentence_idx = indexing.create_sentence_window_index(chunks)
                    
                    st.session_state.indices = {
                        "vector": vector_idx,
                        "sentence": sentence_idx,
                    }
                    
                    # Store original for reset
                    import copy
                    st.session_state.original_indices = copy.deepcopy(st.session_state.indices)
                    
                    st.session_state.gemini_key = gemini_api_key
                    st.success("✅ Indexed successfully! You can now ask questions.")

# ── Chat Interface ───────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question:"):
    if not enable_web_search and "indices" not in st.session_state:
        st.error("Please upload and index documents first, or enable Web Search!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving and generating…"):
                gemini_key = st.session_state.get("gemini_key", os.getenv("GEMINI_API_KEY"))
                if not gemini_key:
                    st.error("Gemini API key is missing.")
                    st.stop()
                    
                generation = GenerationManager(gemini_key)
                
                if enable_web_search:
                    # Wikipedia exclusive mode
                    with st.spinner("Searching Wikipedia…"):
                        wiki_mgr = WikipediaManager()
                        wiki_summary = wiki_mgr.get_summary(prompt)
                    
                    if wiki_summary:
                        # Create mock nodes from Wikipedia summary to use RAG generation
                        nodes = [{
                            "text": wiki_summary["summary"],
                            "metadata": {
                                "source": wiki_summary["url"],
                                "title": wiki_summary["title"],
                                "type": "wikipedia"
                            }
                        }]
                        response_data = generation.generate_response(prompt, nodes)
                        answer = response_data["answer"]
                        citations = response_data["citations"]
                        
                        st.info(f"📝 **Wikipedia Summary: {wiki_summary['title']}**\n\n{wiki_summary['summary']}\n\n[Read more on Wikipedia]({wiki_summary['url']})")
                    else:
                        answer = f"Sorry, I couldn't find any Wikipedia information for '{prompt}'."
                        citations = []
                else:
                    # Local Document RAG mode
                    retrieval = RetrievalManager(
                        st.session_state.indices["vector"],
                        st.session_state.indices["sentence"],
                    )
                    
                    nodes = retrieval.retrieve_and_rerank(prompt)
                    response_data = generation.generate_response(prompt, nodes)

                    answer = response_data["answer"]
                    citations = response_data["citations"]

                st.markdown(answer)
                if citations:
                    with st.expander("📚 Sources & Citations"):
                        st.markdown(generation.format_citations(citations))

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )
