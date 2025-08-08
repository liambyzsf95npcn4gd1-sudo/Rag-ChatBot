import streamlit as st
import os
import hashlib
from utils.prepare_vectordb import get_vectorstore
import logging

def file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()

def save_docs_to_vectordb(uploaded_files, upload_docs):
    """
    Save uploaded documents to the 'docs' folder and create or update the vectorstore.

    Parameters:
    - uploaded_files (list): List of uploaded files.
    - upload_docs (list): List of names of previously uploaded documents.
    """
    new_files_to_process = []
    if uploaded_files:
        for f in uploaded_files:
            file_bytes = f.read()
            h = file_hash(file_bytes)
            if h in st.session_state.get("processed_files", set()):
                st.write(f"{f.name} — already processed")
                continue

            # Save file to docs/ with a unique name and process it
            file_path = os.path.join("docs", f.name)
            with open(file_path, "wb") as f_out:
                f_out.write(file_bytes)

            st.session_state.setdefault("processed_files", set()).add(h)
            new_files_to_process.append(f.name)

    if new_files_to_process and st.button("Process"):
        with st.spinner("Processing..."):
            logging.info(f"Processing new files: {new_files_to_process}")
            get_vectorstore(new_files_to_process)
            st.success(f"Files processed successfully.")
            # We need to rerun the app to update the UI
            st.rerun()