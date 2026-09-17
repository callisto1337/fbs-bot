# xlsx-converter

Бот для MAX: принимает xlsx-файл и возвращает его обратно (логика форматирования — точка расширения в `app/xlsx_processing.py`, пока не реализована). Доступ выдаётся вручную через админку и ограничен по времени.

## Как это работает

1. После оплаты (вне бота) администратор в админке добавляет запись: номер телефона, срок действия доступа (`access_expires_at`), `is_active=true`.
2. Пользователь открывает бота. Если он ещё не привязан по `max_user_id`, бот просит поделиться номером телефона (кнопка в один тап).
3. После подтверждения номера бот привязывает `max_user_id` к записи в БД — дальше доступ проверяется по нему.
4. Пока доступ активен, пользователь может присылать `.xlsx`-файлы и получать их обратно.
5. По истечении `access_expires_at` (или при `is_active=false`) бот снова просит подтвердить номер и не обрабатывает файлы, пока админ не продлит доступ.

## Стек

FastAPI + SQLAlchemy (async) + Alembic + SQLAdmin + PostgreSQL + Poetry + [`maxapi`](https://github.com/max-messenger/max-botapi-python) (long polling, без вебхука и сертификатов).

## Запуск

1. Скопировать `.env.example` в `.env` и заполнить:
   - `MAX_BOT_TOKEN` — токен бота из кабинета разработчика MAX;
   - `POSTGRES_*` и `DATABASE_URL` — держать в синхронизации (`DATABASE_URL` использует те же логин/пароль/имя базы);
   - `ADMIN_SECRET_KEY` — случайная строка (например, `openssl rand -hex 32`);
   - `ADMIN_USERNAME` / `ADMIN_PASSWORD` — логин в админку.

2. Поднять всё:

   ```bash
   docker compose up -d --build
   ```

   Сервис `migrate` применяет миграции Alembic и завершается, `bot` и `admin` стартуют после него.

3. Админка: `http://<сервер>:8000/admin` (логин/пароль из `.env`).

## Локальная разработка без Docker

```bash
poetry install
poetry run alembic upgrade head          # нужен доступ к Postgres из DATABASE_URL
poetry run python -m app.bot.main        # бот (long polling)
poetry run uvicorn app.admin_app:app --reload   # админка
```

## Структура

```
app/
  config.py        # настройки из .env
  db.py             # async engine/session
  models.py         # модель MaxUser (доступ пользователей MAX)
  admin_app.py       # FastAPI + SQLAdmin
  xlsx_processing.py # точка расширения под форматирование таблиц
  bot/
    access.py        # поиск/привязка пользователя по телефону и max_user_id
    handlers.py       # хендлеры бота (/start, контакт, приём/отдача xlsx)
    main.py           # запуск бота (long polling)
migrations/           # Alembic
```

## Известные нюансы для проверки на реальном токене

- Формат вложения-контакта (`payload.vcf.phone`, `payload.max_info`) и скачивание файла (`bot.download_bytes`) реализованы по исходникам `maxapi` 1.2.2 и прогнаны через импорт-тест, но не проверялись живым вызовом API MAX — стоит один раз руками прогнать сценарий "поделиться номером" → "прислать xlsx" на реальном боте.
