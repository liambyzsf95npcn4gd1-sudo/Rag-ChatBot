import streamlit as st
import os
from utils.save_docs import save_docs_to_vectordb
from utils.session_state import initialize_session_state_variables
from utils.prepare_vectordb import get_vectorstore
from utils.chatbot import chat
from utils.send_email import send_email
from utils.price_merge import load_price_csv, merge_products_with_prices
from langchain_core.documents import Document
import shutil
import logging
from utils.config import GOOGLE_API_KEY, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MANAGER_EMAIL, CHROMA_PERSIST_DIR
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check for required environment variables
if not GOOGLE_API_KEY:
    raise RuntimeError("Missing env var: GOOGLE_API_KEY — please create a .env file with it. You can get a key from https://aistudio.google.com/app/apikey")

class ChatApp:
    """
    A Streamlit application for chatting with PDF and XML documents.

    This class encapsulates the functionality for uploading documents, processing them,
    and enabling users to chat with the documents using a chatbot. It handles the initialization
    of Streamlit configurations and session state variables, as well as the frontend for document
    upload and chat interaction.
    """
    def __init__(self):
        """
        Initializes the ChatApp class.

        This method ensures the existence of the 'docs' folder, sets Streamlit page configurations,
        and initializes session state variables.
        """
        logging.info("Starting ChatApp")
        # Ensure the docs folder exists
        if not os.path.exists("docs"):
            os.makedirs("docs")

        # Configurations and session state initialization
        st.set_page_config(page_title="Chat with your Documents :books:")
        st.title("Chat with your Documents :books:")
        initialize_session_state_variables(st)
        self.docs_files = st.session_state.processed_documents

    def run(self):
        """
        Runs the Streamlit app for chatting with PDFs

        This method handles the frontend for document upload, unlocks the chat when documents are uploaded,
        and locks the chat until documents are uploaded
        """
        upload_docs = os.listdir("docs")
        # Sidebar frontend for document upload
        with st.sidebar:
            st.subheader("Your documents")
            if upload_docs:
                st.write("Uploaded Documents:")
                st.text(", ".join(upload_docs))
            else:
                st.info("No documents uploaded yet.")
            st.subheader("Upload documents")
            uploaded_files = st.file_uploader("Select a document and click on 'Process'", type=['pdf', 'xml'], accept_multiple_files=True)

            if 'last_uploaded_files' not in st.session_state:
                st.session_state['last_uploaded_files'] = []

            if uploaded_files and uploaded_files != st.session_state.last_uploaded_files:
                st.session_state.last_uploaded_files = uploaded_files
                save_docs_to_vectordb(uploaded_files, upload_docs)
                st.rerun()

            st.subheader("Upload Price CSV")
            uploaded_csv = st.file_uploader("Select a CSV with prices", type=['csv'])
            if uploaded_csv and uploaded_csv.name != st.session_state.get("last_uploaded_csv_name"):
                st.session_state["last_uploaded_csv_name"] = uploaded_csv.name
                st.session_state["price_df"] = load_price_csv(uploaded_csv)

            if st.session_state.get("price_df") is not None and st.button("Merge Prices"):
                with st.spinner("Merging prices and updating database..."):
                    # This part assumes that the product data is stored in the vector database
                    # and we can retrieve it to merge with the price data.
                    # This is a simplification. A real implementation would need a more robust
                    # way to get the product data.
                    retrieved_docs = st.session_state.vectordb.get()
                    products = [metadata for metadata in retrieved_docs['metadatas']]
                    merged_products = merge_products_with_prices(products, st.session_state.price_df)

                    # Re-create the vector store with the merged data
                    # This is also a simplification. In a real app, you would update the existing
                    # vector store instead of re-creating it.
                    if os.path.exists(CHROMA_PERSIST_DIR):
                        shutil.rmtree(CHROMA_PERSIST_DIR)

                    # Create new documents with the merged data
                    merged_docs = [
                        Document(page_content=f"ID: {p.get('id', '')}\nName: {p.get('name', '')}\nDescription: {p.get('description', '')}\nPrice: {p.get('price', '')}",
                                 metadata=p)
                        for p in merged_products
                    ]

                    st.session_state.vectordb = get_vectorstore(google_api_key=GOOGLE_API_KEY, persist_directory=CHROMA_PERSIST_DIR, documents=merged_docs, from_session_state=False)
                    st.success("Prices merged and database updated.")
                    st.rerun()

            st.subheader("Database Management")
            if st.button("Rebuild Index"):
                with st.spinner("Rebuilding index..."):
                    if os.path.exists(CHROMA_PERSIST_DIR):
                        shutil.rmtree(CHROMA_PERSIST_DIR)
                    st.session_state.vectordb = get_vectorstore(google_api_key=GOOGLE_API_KEY, persist_directory=CHROMA_PERSIST_DIR, docs_files=upload_docs, from_session_state=False)
                    st.success("Index rebuilt successfully.")
                    st.rerun()

            if st.session_state.chat_history and all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MANAGER_EMAIL]):
                st.subheader("Send chat history")
                recipient_email = st.text_input("Recipient email:")
                if st.button("Send Email"):
                    chat_history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in st.session_state.chat_history])
                    try:
                        send_email("Chat History", chat_history_str, [recipient_email], from_email=SMTP_USER)
                        st.success("Email sent successfully!")
                    except Exception as e:
                        st.error(f"Failed to send email: {e}")

        # Unlocks the chat when document is uploaded
        if self.docs_files or st.session_state.uploaded_pdfs:
            # Check to see if a new document was uploaded to update the vectordb variable in the session state
            if len(upload_docs) > st.session_state.previous_upload_docs_length:
                st.session_state.vectordb = get_vectorstore(upload_docs, GOOGLE_API_KEY, CHROMA_PERSIST_DIR, from_session_state=True)
                st.session_state.previous_upload_docs_length = len(upload_docs)
            st.session_state.chat_history = chat(st.session_state.chat_history, st.session_state.vectordb, GOOGLE_API_KEY)

        # Locks the chat until a document is uploaded
        if not self.docs_files and not st.session_state.uploaded_pdfs:
            st.info("Upload a pdf file to chat with it. You can keep uploading files to chat with, and if you need to leave, you won't need to upload these files again")

if __name__ == "__main__":
    app = ChatApp()
    app.run()