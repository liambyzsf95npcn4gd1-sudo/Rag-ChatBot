from langchain_community.document_loaders import PyPDFLoader, UnstructuredXMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
import os
import logging
from pathlib import Path
from langchain_core.documents import Document
from .xml_parser import parse_products_from_xml

def extract_text(docs_files):
    """
    Extract text from PDF and XML documents.

    Parameters:
    - docs_files (list): List of document filenames.

    Returns:
    - docs: List of text extracted from the documents.
    """
    docs = []
    for doc_file in docs_files:
        file_path = os.path.join("docs", doc_file)
        if doc_file.endswith(".pdf"):
            docs.extend(PyPDFLoader(file_path).load())
        elif doc_file.endswith(".xml"):
            products = parse_products_from_xml(file_path)
            for product in products:
                content = f"ID: {product['id']}\nName: {product['name']}\nDescription: {product['description']}"
                docs.append(Document(page_content=content, metadata={"source": doc_file}))
    return docs

def get_text_chunks(docs):
    """
    Split text into chunks

    Parameters:
    - docs (list): List of text documents

    Returns:
    - chunks: List of text chunks
    """
    # Chunk size is configured to be an approximation to the model limit of 2048 tokens
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=8000, chunk_overlap=800, separators=["\n\n", "\n", " ", ""])
    chunks = text_splitter.split_documents(docs)
    return chunks

def get_vectorstore(google_api_key, persist_directory, docs_files=None, documents=None, from_session_state=False):
    """
    Create or retrieve a vectorstore from documents.

    Parameters:
    - docs_files (list): List of document filenames.
    - from_session_state (bool, optional): Flag indicating whether to load from session state. Defaults to False.

    Returns:
    - vectordb or None: The created or retrieved vectorstore. Returns None if loading from session state and the database does not exist.
    """
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)
    persist_dir = Path(persist_directory)
    persist_dir.mkdir(parents=True, exist_ok=True)

    if from_session_state and persist_dir.exists():
        # Retrieve vectorstore from existing one
        vectordb = Chroma(persist_directory=str(persist_dir), embedding_function=embedding)
        return vectordb
    elif not from_session_state:
        logging.info("Creating new vector store.")
        if documents is None and docs_files is not None:
            documents = extract_text(docs_files)

        if documents is not None:
            chunks = get_text_chunks(documents)
            try:
                # Create vectorstore from chunks and saves it to the folder Vector_DB - Documents
                logging.info("Embedding documents.")
                vectordb = Chroma.from_documents(documents=chunks, embedding=embedding, persist_directory=str(persist_dir))
                return vectordb
            except Exception as e:
                logging.exception("Embedding error")
                raise RuntimeError("Error creating embedding -- check API key and network") from e
    return None