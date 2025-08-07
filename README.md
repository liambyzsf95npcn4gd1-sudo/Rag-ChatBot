# Чат-бот Консультант по товарам

Это приложение представляет собой чат-бота-консультанта, созданного с использованием Google Gemini-Pro, Langchain, ChromaDB и Streamlit. Бот позволяет пользователям получать консультации по ассортименту товаров, задавая вопросы на естественном языке. Он извлекает информацию из предоставленных XML-файлов с данными о товарах и прайс-листа, а также позволяет оформлять заказы.

Ключевые особенности проекта:
- **Загрузка данных**: Пользователь может загрузить XML-файлы с описанием товаров и прайс-лист в формате CSV или XLSX.
- **Консультации по товарам**: Бот отвечает на вопросы, основываясь исключительно на загруженных данных о товарах, их характеристиках и ценах.
- **Оформление заказа**: В интерфейсе предусмотрена форма для отправки заказа, которая включает прикрепление файла с заказом и отправку уведомлений по электронной почте.
- **Интерактивный интерфейс**: Пользовательский интерфейс, созданный с помощью Streamlit, прост в использовании и включает в себя чат, загрузчики файлов и форму заказа.
- **Отслеживание источников**: Для каждого ответа бота в боковой панели отображаются товары, информация о которых была использована.

## RAG - ChatBot Interface: First Boot and In Usage
The very first time the user launches the app, this will be the screen of the app. Note that the user cannot send any messages, since there are no documents uploaded.

![user_interface](Images/user_interface.png)

The next time that the user launches the app, the chat box will be available and there will be a list of the uploaded documents. If the user tries to upload the same document again, the "process" button will not appear. When the user asks a question, the model will give a response based on the question, the content that was retrieved from the database, and the chat history. In the image below, we can see that the model is aware of the chat history, and that the source of the answer is displayed in the sidebar.

![app_in_use](Images/app_in_use.png)

## Как это работает

Основной цикл работы приложения выглядит следующим образом: пользователь загружает данные, задает вопрос, приложение ищет релевантную информацию в векторной базе данных, и эта информация передается большой языковой модели (LLM) для генерации ответа.

1.  **Загрузка данных**: Пользователь загружает XML-файлы с товарами и прайс-лист (CSV/XLSX) через интерфейс. Эти файлы сохраняются в директорию `docs`.
2.  **Парсинг и объединение**: Приложение парсит XML-файлы для извлечения данных о товарах (ID, название, описание, характеристики) и прайс-лист для получения цен. Затем эти данные объединяются для каждого товара.
3.  **Создание документов и эмбеддингов**: Для каждого товара формируется единый текстовый документ. Этот текст преобразуется в векторное представление (эмбеддинг) с помощью модели `GoogleGenerativeAIEmbeddings`.
4.  **Сохранение в векторную базу**: Полученные эмбеддинги сохраняются в локальную векторную базу данных `ChromaDB` в директории `Vector_DB_Products`. При последующих запусках приложение будет использовать уже существующую базу.
5.  **Поиск по сходству**: Когда пользователь задает вопрос, он также преобразуется в вектор. Приложение сравнивает этот вектор с векторами в базе данных и находит наиболее семантически близкие документы (товары).
6.  **Генерация ответа**: Найденные документы вместе с историей чата и вопросом пользователя передаются модели `Gemini-Pro`, которая генерирует развернутый ответ на основе предоставленного контекста.
7.  **Отправка заказа**: При заполнении формы заказа приложение использует модуль `smtplib` для отправки писем менеджеру и клиенту.

## App Usage
To install and use the app, an API key from Google will be needed. For this, you can click [here](https://aistudio.google.com/app/apikey). Accept the terms, and if the option to create an API key is not selectable, just reload the page. Click on "Create API Key" and then click on "Create API key in new project" and copy the key. It's recommended to paste the key into a new txt file or something, so you have easy access.
Also, to use the app, it's assumed that you have python installed

### Шаг 1: Создайте файл .env
В корневой директории проекта создайте файл с именем `.env`. Этот файл будет содержать ваши секретные ключи и настройки. Скопируйте в него следующий шаблон и подставьте свои значения.

```env
# Ключ для доступа к Google Gemini API
GOOGLE_API_KEY = "ВАШ_API_КЛЮЧ_GOOGLE"

# Настройки для отправки почты через SMTP
SMTP_HOST = "smtp.example.com"
SMTP_PORT = 587
SMTP_USER = "your_email@example.com"
SMTP_PASS = "your_email_password"

# Email менеджера для получения заказов
MANAGER_EMAIL = "manager@example.com"
```

**Важно:**
-   Замените `ВАШ_API_КЛЮЧ_GOOGLE` на ваш реальный ключ от Google AI Studio.
-   Укажите корректные данные вашего SMTP-сервера для отправки почты.
-   `MANAGER_EMAIL` — это адрес, на который будут приходить уведомления о новых заказах.

### Step 2: Install Packages
Open a terminal in this folder. You can do this by holding the shift key on the keyboard and right-clicking on the screen. An option to open a terminal should appear. In the terminal, write this to install all the requirements for the app:

```shell
pip install -r requirements.txt
```

### Step 3: Run the app
In this same terminal, run this command to startup the app:

```shell
streamlit run app/app.py
```

A new window on your web browser should automatically appear, with the app ready to be used. To stop the app, simply press CTR+C on the terminal. A message of "stopping" will appear, and the app will shutdown
