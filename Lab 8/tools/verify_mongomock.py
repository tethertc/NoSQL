#!/usr/bin/env python3
"""Проверка логики запросов из scripts/03_queries.js на эмуляторе mongomock.

ВАЖНО: это НЕ запуск на настоящем MongoDB. Скрипт повторяет те же фильтры и
конвейеры на тех же данных (data/seed.json), чтобы подтвердить ожидаемые
результаты. Индексы и EXPLAIN эмулятор не проверяет — для них нужен mongosh.
Запуск из корня lab8:  python3 tools/verify_mongomock.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import mongomock

ROOT = Path(__file__).resolve().parent.parent


def dt(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).replace(tzinfo=None)


def load():
    data = json.loads((ROOT / "data" / "seed.json").read_text(encoding="utf-8"))
    db = mongomock.MongoClient().lab8_iot
    for d in data["devices"]:
        d["last_reading"]["ts"] = dt(d["last_reading"]["ts"])
    for r in data["readings"] + data["events"]:
        r["ts"] = dt(r["ts"])
    db.devices.insert_many(data["devices"])
    db.readings.insert_many(data["readings"])
    db.events.insert_many(data["events"])
    return db


failed = 0


def check(name, cond, detail=""):
    global failed
    print(("OK:   " if cond else "FAIL: ") + name + (f"  -> {detail}" if detail else ""))
    if not cond:
        failed += 1


db = load()
check("Данные загружены: 6 устройств, 144 показания, 12 событий",
      (db.devices.count_documents({}), db.readings.count_documents({}), db.events.count_documents({}))
      == (6, 144, 12))

# Q1
d = db.devices.find_one({"_id": "dev-001"}, {"name": 1, "last_reading": 1})
print("Q1:", d)
check("Q1. last_reading dev-001 = 23:00, 2.8 °C",
      d["last_reading"]["ts"] == dt("2026-11-01T23:00:00Z") and d["last_reading"]["temp_c"] == 2.8)
ctl = list(db.readings.find({"device_id": "dev-001"}).sort("ts", -1).limit(1))[0]
check("Q1 (контроль). Совпадает с последним в readings", ctl["temp_c"] == d["last_reading"]["temp_c"])

# Q2
q2 = list(db.readings.find(
    {"device_id": "dev-003", "ts": {"$gte": dt("2026-11-01T06:00:00Z"), "$lt": dt("2026-11-01T12:00:00Z")}},
    {"_id": 0, "ts": 1, "temp_c": 1}).sort("ts", 1))
print("Q2:", [(x["ts"].strftime("%H:%M"), x["temp_c"]) for x in q2])
check("Q2. 6 показаний за [06:00; 12:00), верхняя граница не включена",
      len(q2) == 6 and q2[0]["ts"].hour == 6 and q2[-1]["ts"].hour == 11)

# Q3
q3 = list(db.devices.find({"location.site": "Almaty-Lab", "status": "active"}, {"name": 1}))
print("Q3:", [(x["_id"], x["name"]) for x in q3])
check("Q3. Два активных устройства площадки Almaty-Lab", sorted(x["_id"] for x in q3) == ["dev-001", "dev-002"])

# Q4
db.events.insert_one({"device_id": "dev-002", "ts": dt("2026-11-02T00:00:00Z"), "type": "high_temp",
                      "severity": "critical", "message": "Температура выше порога 30 °C", "acknowledged": False})
check("Q4. Событие записано (13 событий)", db.events.count_documents({}) == 13)

# Q5
new_ts = dt("2026-11-02T00:00:00Z")
db.readings.insert_one({"device_id": "dev-002", "ts": new_ts, "temp_c": 31.4, "humidity_pct": 44.0, "battery_pct": 87})
r = db.devices.update_one({"_id": "dev-002", "last_reading.ts": {"$lt": new_ts}},
                          {"$set": {"last_reading": {"ts": new_ts, "temp_c": 31.4, "humidity_pct": 44.0, "battery_pct": 87}}})
check("Q5. last_reading dev-002 обновлён (matched=1, modified=1)", (r.matched_count, r.modified_count) == (1, 1))
r2 = db.devices.update_one({"_id": "dev-002", "last_reading.ts": {"$lt": dt("2026-11-01T10:00:00Z")}},
                           {"$set": {"last_reading.temp_c": 0}})
check("Q5 (граница). Запоздавшее показание не затирает свежее (matched=0)", r2.matched_count == 0)
check("Q5 (проверка). last_reading.temp_c = 31.4",
      db.devices.find_one({"_id": "dev-002"})["last_reading"]["temp_c"] == 31.4)

# Q6
q6 = list(db.readings.aggregate([
    {"$match": {"ts": {"$gte": dt("2026-11-01T00:00:00Z"), "$lt": dt("2026-11-02T00:00:00Z")}}},
    {"$group": {"_id": "$device_id", "n": {"$sum": 1}, "avg_temp": {"$avg": "$temp_c"},
                "min_temp": {"$min": "$temp_c"}, "max_temp": {"$max": "$temp_c"}}},
    {"$lookup": {"from": "devices", "localField": "_id", "foreignField": "_id", "as": "dev"}},
    {"$unwind": "$dev"},
    # В scripts/03_queries.js здесь avg_temp: {$round: ['$avg_temp', 2]}; mongomock оператор $round
    # не поддерживает, поэтому ниже округляем в Python (остальной конвейер идентичен).
    {"$project": {"_id": 1, "n": 1, "avg_temp": 1, "min_temp": 1, "max_temp": 1,
                  "temp_max_threshold": "$dev.thresholds.temp_max",
                  "over_threshold": {"$gt": ["$max_temp", "$dev.thresholds.temp_max"]}}},
    {"$sort": {"max_temp": -1}},
]))
for x in q6:
    x["avg_temp"] = round(x["avg_temp"], 2)
print("Q6:")
for x in q6:
    print("   ", x)
check("Q6. По 24 показания у каждого из 6 устройств", len(q6) == 6 and all(x["n"] == 24 for x in q6))
over = sorted(x["_id"] for x in q6 if x["over_threshold"])
check("Q6. Превышение порога за сутки: " + ", ".join(over), over == ["dev-002"], str(over))

# Q7
q7 = list(db.events.aggregate([
    {"$match": {"acknowledged": False}},
    {"$group": {"_id": "$severity", "n": {"$sum": 1}}},
    {"$sort": {"n": -1, "_id": 1}},
]))
print("Q7:", q7)
check("Q7. Неподтверждённые: critical 3, info 2, warning 2",
      {x["_id"]: x["n"] for x in q7} == {"critical": 3, "info": 2, "warning": 2})

# Q8
flt = {"severity": "info", "acknowledged": True, "ts": {"$lt": dt("2026-11-01T06:00:00Z")}}
before = db.events.count_documents(flt)
check("Q8a. Контрольная выборка: 3 события к удалению", before == 3)
res = db.events.delete_many(flt) if 0 < before <= 10 else None
check("Q8b. Удалено 3, осталось 10 событий", res is not None and res.deleted_count == 3 and db.events.count_documents({}) == 10)
check("Q8 (граница). Не затронуты неподтверждённые info и подтверждённые warning",
      db.events.count_documents({"severity": "info", "acknowledged": False}) == 2
      and db.events.count_documents({"severity": "warning", "acknowledged": True}) == 2)

# Q9
db.devices.update_one({"_id": "dev-006"}, {"$set": {"status": "decommissioned"}})
q9 = {x["_id"]: x["n"] for x in db.devices.aggregate([{"$group": {"_id": "$status", "n": {"$sum": 1}}}])}
check("Q9. dev-006 выведен из эксплуатации: active 5, decommissioned 1",
      q9 == {"active": 5, "decommissioned": 1}, str(q9))
check("Q9. История показаний dev-006 сохранена (24 записи)", db.readings.count_documents({"device_id": "dev-006"}) == 24)

print(f"\nИтого провалено: {failed}")
sys.exit(0 if failed == 0 else 1)
