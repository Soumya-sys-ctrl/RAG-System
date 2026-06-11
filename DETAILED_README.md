# 🚀 Advanced RAG & Web-Search Conversational Assistant

Welcome to the **Advanced Multi-Source RAG System**! This application is designed to behave like a highly intelligent, context-aware chatbot that can query your local documents (PDFs and CSVs) or fetch real-time information from Wikipedia.

It is built completely from scratch using Python, utilizing **Google Gemini** for its cognitive capabilities (both for generating embeddings and deriving the final conversational answers).

---

## 🎯 What Does This Project Do?

The application solves a common problem: accessing specific information scattered across long PDFs, large CSV spreadsheets, or the open internet, without having to manually read through everything. 

It has **two primary modes of operation**:

1. **Local Document RAG (Retrieval-Augmented Generation):**
   - You can upload multiple PDFs or CSV files through the web interface.
   - The application automatically extracts text, chunks it into manageable and semantically meaningful blocks, and generates vector embeddings using Gemini's Embedding Model.
   - These chunks are saved into an in-memory Vector Database.
   - When you ask a question, the application mathematically finds the most relevant document chunks to your question and passes them directly to Gemini. Gemini synthesizes a perfect, conversational answer with explicit citations (showing exactly which document and page number the answer came from).

2. **Web Search / Wikipedia Mode:**
   - If you want general knowledge that is not in your documents, you can toggle the "Web Search" mode.
   - The system intercepts your question, performs a background web search, scrapes the relevant Wikipedia article, and uses it as the context to formulate an accurate and highly-informative answer.

---

## 🏗️ Architecture & Component Breakdown

- **Frontend (`app.py`):** Built with **Streamlit**, providing a clean, responsive, and easy-to-use chat interface.
- **Knowledge Ingestion (`src/ingestion.py` / PyPDF & CSV):** Handles the extraction of messy raw text from uploaded files and intelligently segments it.
- **Vector Search Engine (`numpy`):** Stores embedding vectors and performs blazing fast Cosine Similarity calculations to find document chunks relevant to the user's prompt.
- **Gemini LLM Engine (`requests` directly to the API):** We bypass heavy third-party frameworks like LangChain or LlamaIndex and integrate directly with Gemini's API. This ensures maximum speeds and a deep understanding of how RAG is fundamentally implemented under the hood.

---

## 🛠️ Step-by-Step Running Procedures

Follow these precise steps to get the application running on your local machine.

### Prerequisites
- Python 3.8 to Python 3.11 installed.
- A **Google Gemini API Key**. (You can get one from Google AI Studio).

### 1. Configure the Environment variables
For convenience, you can either input your Gemini API Key directly into the running Streamlit UI sidebar, or you can permanently add it to your environment by modifying `.env`.
Open the `.env` file (or rename `.env.example` to `.env`) and add:
```env
GEMINI_API_KEY=your_actual_api_key_goes_here
```

### 2. Install the necessary dependencies
Ensure you are in the project folder (`RAG_Project_no.110/RAG_Project_no.110`). Open your terminal/command prompt and run:
```bash
pip install -r requirements.txt
```
*(This installs `streamlit`, `pypdf`, `requests`, `duckduckgo-search`, `numpy`, and `beautifulsoup4`)*

### 3. Launch the Application!
Once the dependencies are installed, start the Streamlit server by running:
```bash
streamlit run app.py
```

### 4. Interact with the UI
- Your browser will automatically open a tab pointing to `http://localhost:8501`.
- Wait for the app to initialize.
- On the left sidebar, verify your API Key is inserted.
- Upload any PDF or CSV file.
- Try asking questions about the document in the central chat input.
- Check the "Toggle Web Search" toggle in the sidebar and ask a general knowledge question (like "Who won the 2022 FIFA World Cup?").

Enjoy querying your intelligence base!