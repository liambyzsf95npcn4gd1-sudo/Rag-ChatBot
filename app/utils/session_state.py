import os
from utils.prepare_vectordb import get_vectorstore

def get_file_paths(directory):
    """
    Scans a directory and categorizes files into XMLs and a price list.
    """
    if not os.path.exists(directory):
        return [], None

    all_files = os.listdir(directory)
    xml_files = [f for f in all_files if f.endswith('.xml')]
    price_file = next((f for f in all_files if f.endswith(('.csv', '.xlsx'))), None)
    return xml_files, price_file

def initialize_session_state_variables(st):
    """
    Initialize session state variables for the Streamlit application.
    """
    processed_xmls, processed_price_file = get_file_paths("docs")

    # Centralized session state initialization
    defaults = {
        "chat_history": [],
        "processed_xmls": processed_xmls,
        "processed_price_file": processed_price_file,
        "vectordb": None,
        "previous_file_count": len(processed_xmls) + (1 if processed_price_file else 0)
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Special handling for vectordb initialization
    if st.session_state.vectordb is None:
        if processed_xmls and processed_price_file:
            # Note: get_vectorstore expects full paths, but we store only filenames in session state
            # The calling function in app.py will be responsible for constructing full paths
            st.session_state.vectordb = get_vectorstore(
                product_xml_paths=[os.path.join("docs", f) for f in processed_xmls],
                price_file_path=os.path.join("docs", processed_price_file),
                from_session_state=True
            )
