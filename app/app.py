import streamlit as st
import os
import logging
import pandas as pd
from utils.session_state import initialize_session_state_variables
from utils.prepare_vectordb import create_vectorstore
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

        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

        initialize_session_state_variables(st)

    def _save_uploaded_file(self, uploaded_file):
        """Saves a single uploaded file to the 'docs' directory with error handling."""
        try:
            if not os.path.exists("docs"):
                os.makedirs("docs")
            file_path = os.path.join("docs", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            return file_path, None
        except Exception as e:
            return None, f"Не удалось сохранить файл {uploaded_file.name}: {e}"

    def _process_data(self, xml_files_to_process, price_file_to_process):
        """Helper function to run the data processing and vectordb creation."""
        with st.spinner("Обработка файлов..."):
            xml_paths = [os.path.join("docs", f) for f in xml_files_to_process]
            price_path = os.path.join("docs", price_file_to_process)

            st.session_state.vectordb, products_df = create_vectorstore(xml_paths, price_path)
            if products_df:
                st.session_state.product_dataframe = pd.DataFrame(products_df)

            logging.info(f"Vectorstore created/updated with {len(xml_files_to_process)} XML files and price file {price_file_to_process}.")
            st.success("Данные успешно обработаны!")
            st.rerun()

    def run(self):
        """
        Runs the main application logic for the Streamlit UI.
        """
        with st.sidebar:
            st.subheader("Управление данными")

            uploaded_xml_files = st.file_uploader(
                "Загрузите XML файлы с товарами", type=['xml'], accept_multiple_files=True, key="xml_uploader"
            )
            uploaded_price_file = st.file_uploader(
                "Загрузите прайс-лист (CSV/XLSX)", type=['csv', 'xlsx'], accept_multiple_files=False, key="price_uploader"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Обработать (заменить)"):
                    if not uploaded_xml_files or not uploaded_price_file:
                        st.warning("Для полной замены нужны и XML, и прайс-лист.")
                    else:
                        # Clear old files from docs and session
                        st.session_state.processed_xmls = []
                        st.session_state.processed_price_file = None
                        # (Optional: add logic to delete files from disk if desired)

                        # Save new files
                        for f in uploaded_xml_files:
                            _, error = self._save_uploaded_file(f)
                            if error: st.error(error)
                        _, error = self._save_uploaded_file(uploaded_price_file)
                        if error: st.error(error)

                        st.session_state.processed_xmls = [f.name for f in uploaded_xml_files]
                        st.session_state.processed_price_file = uploaded_price_file.name
                        self._process_data(st.session_state.processed_xmls, st.session_state.processed_price_file)

            with col2:
                if st.button("Добавить к текущим"):
                    if not uploaded_xml_files:
                        st.warning("Загрузите XML-файлы для добавления.")
                    else:
                        # Add new unique files to the list
                        new_files_to_add = [f for f in uploaded_xml_files if f.name not in st.session_state.processed_xmls]
                        for f in new_files_to_add:
                            _, error = self._save_uploaded_file(f)
                            if error: st.error(error)

                        st.session_state.processed_xmls.extend([f.name for f in new_files_to_add])

                        # If a new price file is uploaded, it replaces the old one
                        if uploaded_price_file:
                            _, error = self._save_uploaded_file(uploaded_price_file)
                            if error: st.error(error)
                            st.session_state.processed_price_file = uploaded_price_file.name

                        if st.session_state.processed_xmls and st.session_state.processed_price_file:
                            self._process_data(st.session_state.processed_xmls, st.session_state.processed_price_file)
                        else:
                            st.warning("Для обработки необходим хотя бы один XML и прайс-лист.")

            # Display currently processed files
            st.markdown("---")
            st.write("Активные файлы данных:")
            if st.session_state.get("processed_xmls"):
                st.write("Товары (XML):")
                st.json(st.session_state.processed_xmls, expanded=False)
            if st.session_state.get("processed_price_file"):
                st.write("Прайс-лист:")
                st.info(st.session_state.processed_price_file)

            if st.session_state.get("product_dataframe") is not None:
                st.markdown("---")
                st.write("Загруженные товары:")
                st.dataframe(st.session_state.product_dataframe, use_container_width=True)

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
                        # Validate the order file before sending
                        is_valid, validation_message = self._validate_order_file(order_file)
                        if not is_valid:
                            st.error(f"Ошибка в файле заказа: {validation_message}")
                        else:
                            # Call the email sending function
                            with st.spinner("Отправка заказа..."):
                                success, message = send_order_email(
                                    name=name,
                                    client_email=email,
                                    order_file_name=order_file.name,
                                    order_file_content=order_file.getvalue()
                                )
                            if success:
                                logging.info(f"Order submitted successfully by {name} ({email}).")
                                st.success(f"Заказ от {name} успешно отправлен! Мы скоро свяжемся с вами.")
                            else:
                                logging.error(f"Failed to send order for {name} ({email}). Reason: {message}")
                                st.error(f"Не удалось отправить заказ. {message}")
                    else:
                        st.error("Пожалуйста, заполните все поля и прикрепите файл заказа.")

    def _validate_order_file(self, order_file):
        """
        Validates the structure of the uploaded order file.
        Assumes CSV for now, checks for 'товар' and 'кол-во' columns.
        """
        try:
            # We need to reset the file pointer after reading it
            order_file.seek(0)
            df = pd.read_csv(order_file)
            required_columns = {"товар", "кол-во"}
            if not required_columns.issubset(df.columns):
                return False, f"Отсутствуют необходимые колонки. Требуются: {', '.join(required_columns)}"
            # Reset pointer again so getvalue() works later
            order_file.seek(0)
            return True, "Файл заказа корректен."
        except Exception as e:
            return False, f"Не удалось прочитать файл. Убедитесь, что это корректный CSV. Ошибка: {e}"

        # Main chat interface
        if st.session_state.get("vectordb"):
            st.session_state.chat_history = chat(st.session_state.chat_history, st.session_state.vectordb)
        else:
            st.info("Пожалуйста, загрузите XML-файлы с товарами и прайс-лист в меню слева, а затем нажмите 'Обработать данные', чтобы начать чат.")

if __name__ == "__main__":
    app = ProductChatApp()
    app.run()
