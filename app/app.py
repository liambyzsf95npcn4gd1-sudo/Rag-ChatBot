import streamlit as st
import os
from utils.session_state import initialize_session_state_variables
from utils.prepare_vectordb import get_vectorstore
from utils.chatbot import chat
from utils.email_sender import send_order_email

class ProductChatApp:
    """
    A Streamlit application for chatting with product data.
    """
    def __init__(self):
        """
        Initializes the application, sets page config, and session state.
        """
        st.set_page_config(page_title="Чат-бот Консультант", page_icon=":robot_face:")
        st.title("Чат-бот Консультант по товарам :shopping_bags:")
        initialize_session_state_variables(st)

    def _save_uploaded_file(self, uploaded_file):
        """Saves a single uploaded file to the 'docs' directory."""
        if not os.path.exists("docs"):
            os.makedirs("docs")
        file_path = os.path.join("docs", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        return file_path

    def run(self):
        """
        Runs the main application logic for the Streamlit UI.
        """
        # Sidebar for data upload and management
        with st.sidebar:
            st.subheader("Управление данными")

            # File uploaders
            xml_files = st.file_uploader(
                "Загрузите XML файлы с товарами",
                type=['xml'],
                accept_multiple_files=True,
                key="xml_uploader"
            )
            price_file = st.file_uploader(
                "Загрузите прайс-лист (CSV/XLSX)",
                type=['csv', 'xlsx'],
                accept_multiple_files=False,
                key="price_uploader"
            )

            # Determine if processing is possible
            can_process = (xml_files or st.session_state.get("processed_xmls")) and \
                          (price_file or st.session_state.get("processed_price_file"))

            if can_process:
                if st.button("Обработать данные"):
                    with st.spinner("Обработка файлов..."):
                        # Save new files and update session state
                        if xml_files:
                            # If new XMLs are uploaded, we replace the old list
                            st.session_state.processed_xmls = []
                            for f in xml_files:
                                self._save_uploaded_file(f)
                                st.session_state.processed_xmls.append(f.name)

                        if price_file:
                            self._save_uploaded_file(price_file)
                            st.session_state.processed_price_file = price_file.name

                        # Re-create vector store
                        xml_paths = [os.path.join("docs", f) for f in st.session_state.processed_xmls]
                        price_path = os.path.join("docs", st.session_state.processed_price_file)

                        st.session_state.vectordb = get_vectorstore(xml_paths, price_path, from_session_state=False)
                        st.success("Данные успешно обработаны!")
                        st.rerun()

            # Display currently processed files
            st.markdown("---")
            st.write("Активные файлы данных:")
            if st.session_state.get("processed_xmls"):
                st.write("Товары (XML):")
                st.json(st.session_state.processed_xmls, expanded=False)
            if st.session_state.get("processed_price_file"):
                st.write("Прайс-лист:")
                st.info(st.session_state.processed_price_file)

            # Order form
            st.markdown("---")
            st.subheader("Оформить заказ")
            with st.form("order_form", clear_on_submit=True):
                name = st.text_input("Ваше имя")
                email = st.text_input("Email для уведомления")
                order_file = st.file_uploader("Загрузите файл заказа (CSV/JSON/XML)")
                submitted = st.form_submit_button("Отправить заказ")

                if submitted:
                    if name and email and order_file:
                        # Call the email sending function
                        success, message = send_order_email(
                            name=name,
                            client_email=email,
                            order_file_name=order_file.name,
                            order_file_content=order_file.getvalue()
                        )
                        if success:
                            st.success(f"Заказ от {name} успешно отправлен! Мы скоро свяжемся с вами.")
                        else:
                            st.error(f"Не удалось отправить заказ. {message}")
                    else:
                        st.error("Пожалуйста, заполните все поля и прикрепите файл заказа.")

        # Main chat interface
        if st.session_state.get("vectordb"):
            st.session_state.chat_history = chat(st.session_state.chat_history, st.session_state.vectordb)
        else:
            st.info("Пожалуйста, загрузите XML-файлы с товарами и прайс-лист в меню слева, а затем нажмите 'Обработать данные', чтобы начать чат.")

if __name__ == "__main__":
    app = ProductChatApp()
    app.run()
