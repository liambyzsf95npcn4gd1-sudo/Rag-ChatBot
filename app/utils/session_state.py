import os
from utils.prepare_vectordb import get_vectorstore
from utils.save_docs import file_hash

def initialize_session_state_variables(st):
    """
    Initialize session state variables for the Streamlit application.

    Parameters:
    - st: Streamlit's DeltaGenerator object.
    """
    upload_docs = os.listdir("docs")

    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()
        for filename in upload_docs:
            file_path = os.path.join("docs", filename)
            if os.path.isfile(file_path):
                with open(file_path, "rb") as f:
                    st.session_state.processed_files.add(file_hash(f.read()))

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "uploaded_pdfs" not in st.session_state:
        st.session_state.uploaded_pdfs = []

    if "processed_documents" not in st.session_state:
        st.session_state.processed_documents = upload_docs

    if "vectordb" not in st.session_state:
        st.session_state.vectordb = get_vectorstore(upload_docs, from_session_state=True)

    if "previous_upload_docs_length" not in st.session_state:
        st.session_state.previous_upload_docs_length = len(upload_docs)