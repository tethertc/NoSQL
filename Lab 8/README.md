# Лабораторная работа 8, вариант 6: IoT-мониторинг (MongoDB)

Прототип хранилища для устройств, показаний и событий. СУБД: MongoDB (в сравнении рассматривалась Apache Cassandra).

## Что нужно

- Docker Desktop (или локально установленный MongoDB)
- `mongosh` (MongoDB Shell)
- Python 3 — только для необязательной проверки `tools/verify_mongomock.py`

## Запуск MongoDB (порт открыт только на localhost)

```
docker run --name lab8-mongo -p 127.0.0.1:27017:27017 -d mongo:8
mongosh "mongodb://127.0.0.1:27017" --eval "db.version()"
```

Вторая команда проверяет соединение и показывает версию — запишите её в отчёт (раздел 7).

## Порядок выполнения (из корня lab8)

```
mongosh "mongodb://127.0.0.1:27017" --file scripts/01_schema_indexes.js
mongosh "mongodb://127.0.0.1:27017" --file scripts/02_seed.js
mongosh "mongodb://127.0.0.1:27017" --file scripts/03_queries.js
mongosh "mongodb://127.0.0.1:27017" --file scripts/04_explain.js
```

- `01` создаёт коллекции `devices`, `readings`, `events` в базе `lab8_iot`, правила валидации и индексы.
- `02` загружает тестовые данные: 6 устройств, 144 показания, 12 событий (синтетические).
- `03` выполняет ключевые запросы Q1–Q9 (чтение, запись, изменение, аналитика, безопасное удаление).
- `04` сравнивает планы выполнения (EXPLAIN): с индексом и без, два способа получить последнее показание.

Скрипт `03` изменяет данные. Чтобы запустить его повторно, сначала снова выполните `02_seed.js`.

## Остановка и очистка

```
docker rm -f lab8-mongo
```

## Проверка логики без MongoDB (необязательно)

```
pip install pymongo mongomock
python3 tools/verify_mongomock.py
```

Скрипт повторяет запросы Q1–Q9 на эмуляторе `mongomock` и подтверждает ожидаемые результаты (17 проверок). Это не запуск на настоящем MongoDB: индексы и EXPLAIN эмулятор не проверяет.

## Состав

```
lab8/
├── scripts/01_schema_indexes.js  02_seed.js  03_queries.js  04_explain.js
├── tools/generate_seed.py        verify_mongomock.py
├── data/seed.json
└── README.md
```

`02_seed.js` создаётся командой `python3 tools/generate_seed.py` (данные детерминированы, случайные числа не используются).
