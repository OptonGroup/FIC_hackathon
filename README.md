

![fin-viision-4](https://github.com/user-attachments/assets/87532c8a-7e44-4a18-ab32-63801b0d360a)


# FinVision 👁️‍🗨️ 

## Описание 📝

**FinVision** – это простое и удобное веб-приложение, которое помогает пользователям контролировать свои доходы и расходы. Следите за финансами, организуйте свои записи и анализируйте расходы с помощью наглядной статистики. 📈📉 💹

# Демо версия: http://194.87.151.189:8000 (скрины ниже)
---

## Основные функции 🚀 ⭐️

### Авторизация пользователей 🔒 🔐  
- **Регистрация и вход:** Защищенный доступ для хранения данных в безопасности. 🛡️

### Управление транзакциями 💵 💰  
- **Добавление записей:** Создание записей о доходах и расходах с указанием:
  - Суммы 💲 💸
  - Категории (например, «Продукты», «Транспорт», «Развлечения») 🛒 🚗 🎮
  - Даты 🗓️ ⏰
- **Редактирование/Удаление:** Легкое изменение или удаление записей. ✏️ 🗑️
- **Автоматическое определение банка:** Система автоматически определяет банк по номеру карты 🏦
- **Календарь транзакций:** Удобный календарь с возможностью просмотра транзакций по дням 📅
- **Курсы валют:** Актуальные курсы основных валют с автоматическим обновлением 💱
- **Умная сортировка:** Гибкая система фильтрации и сортировки всех транзакций 🔄

### ИИ-помощник 🤖
- **Финансовый консультант:** Чат-бот на основе ИИ для персональных финансовых рекомендаций
- **Анализ расходов:** Умный анализ ваших трат и предложения по оптимизации
- **Финансовые стратегии:** Персонализированные стратегии накопления и инвестирования

### Аналитика и визуализация 📊
- **Интерактивные графики:** Динамические графики доходов и расходов
- **Круговые диаграммы:** Наглядное отображение распределения трат по категориям
- **Прогнозирование:** Умное прогнозирование будущих расходов на основе истории
- **Тепловые карты:** Визуализация интенсивности трат по дням и категориям

### Просмотр транзакций 📋 📑  
- **Список транзакций:** Полный список ваших записей. 📝
- **Фильтры:** Поиск записей по дате или категории для удобной навигации. 🔍

### Статистика 📊 📈  
- **Сводка доходов и расходов:** Общая сумма за выбранный период. 💹
- **Распределение по категориям:** Наглядные диаграммы или таблицы для анализа. 🥧 📊 📉

### Управление кредитами 💳 🏦
- **Добавление кредитов:** Создание записей о кредитах 💰
- **Редактирование/Удаление:** Изменение или удаление кредитных записей 📝


---

## Технологический стек 🛠️ ⚙️

### Frontend 🌐 🎨
- **Фреймворк:** React.js ⚛️ 
- **Функционал:** 🎯
  - Интуитивно понятный интерфейс. 🖥️
  - Удобные формы для ввода и редактирования данных. ⌨️
  - Динамические таблицы и диаграммы. 📊

### Backend 🔙 ⚡️
- **Фреймворк:** FastAPI 🐍
- **База данных:** Postgres + SQLAlchemy ORM 🗄️
- **Хеширование:** SHA-256 для безопасного хранения данных 🔒

---

## API Эндпоинты 🛣️ 🔌

### Пользователи (Users) 👥
- `POST /users/sign_in` – Регистрация нового пользователя 📝
- `POST /users/login` – Вход в систему 🔑
- `POST /users/logout` – Выход из системы 🚪
- `POST /users/logout_all` – Выход из всех сессий 🔐
- `GET /users/check_session` – Проверка активности сессии ✅
- `GET /users/sessions_count` – Получение количества активных сессий 🔢
- `GET /users/profile` – Получение информации о профиле 👤
- `PUT /users/update` – Обновление данных пользователя ✏️

### Экспорт данных 📤
- `GET /users/export/all_transactions` – Экспорт всех транзакций 📊

### Цели (Targets) 🎯
- `POST /targets/` – Создание новой цели ➕
- `PUT /targets/{target_id}` – Изменение существующей цели ✏️
- `DELETE /targets/{target_id}` – Удаление цели ❌

### Транзакции (Transactions) 💸
- `POST /transactions/` – Создание новой транзакции ➕
- `PUT /transactions/{transaction_id}` – Изменение существующей транзакции ✏️
- `DELETE /transactions/{transaction_id}` – Удаление транзакции ❌

### Кредиты (Credits) 💳
- `POST /credits/` – Создание нового кредита ➕
- `PUT /credits/{credit_id}` – Изменение существующего кредита ✏️
- `DELETE /credits/{credit_id}` – Удаление кредита ❌

---

## Установка и запуск 🖥️ ⚡️

### Предварительные требования 📋
1. **Python:** Убедитесь, что Python 3.8+ установлен на вашем компьютере. 🐍
2. **PostgreSQL/Sqlite:** База данных PostgreSQL или Sqlite для локального запуска. 🗄️
3. **Nginx:** Веб-сервер Nginx для продакшн-окружения. 🌐

### Шаги для запуска через Django development server 👣
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-repo/personal-finance-tracker.git
   cd personal-finance-tracker
   ```
2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # для Linux/Mac
   venv\Scripts\activate     # для Windows
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Примените миграции:
   ```bash
   python manage.py migrate
   ```
5. Запустите сервер разработки:
   ```bash
   python manage.py runserver
   ```
6. Откройте приложение в браузере по адресу `http://localhost:8000`. 🌍

### Запуск через Uvicorn 🚀
1. Установите Uvicorn:
   ```bash
   pip install uvicorn
   ```
2. Запустите приложение через Uvicorn:
   ```bash
   uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4
   ```
   
### Запуск через Nginx (продакшн) 🌐
1. Установите и настройте Nginx:
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. Создайте конфигурационный файл:
   ```bash
   sudo nano /etc/nginx/sites-available/finvision
   ```

3. Добавьте базовую конфигурацию:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /static/ {
           alias /path/to/your/static/;
       }

       location /media/ {
           alias /path/to/your/media/;
       }
   }
   ```

4. Создайте символическую ссылку:
   ```bash
   sudo ln -s /etc/nginx/sites-available/finvision /etc/nginx/sites-enabled
   ```

5. Проверьте конфигурацию и перезапустите Nginx:
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Лицензия 📜 ⚖️

Этот проект распространяется по лицензии MIT. Подробности в файле `LICENSE`. 📄

---

**Начните управлять своими финансами уже сегодня!** 🌟 💫 ✨ 💰

## Скриншоты

![git_screen](https://github.com/user-attachments/assets/e3f6bb72-046d-4390-8263-abcc9876a693)

