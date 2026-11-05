#!/usr/bin/env python3
"""Генерирует детерминированные синтетические данные для лаб. работы 8 (вариант 6, IoT).

Результат:
  data/seed.json       — данные в JSON (для проверки в tools/verify_mongomock.py)
  scripts/02_seed.js   — тот же набор в виде скрипта для mongosh
Запуск из корня lab8:  python3 tools/generate_seed.py
"""
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAY = datetime(2026, 11, 1, tzinfo=timezone.utc)

# (id, name, site, room, base_temp, amp, temp_max, firmware)
DEVICES = [
    ("dev-001", "Холодильная камера 1", "Almaty-Lab", "A-101", 4.0, 1.0, 8.0, "1.4.2"),
    ("dev-002", "Серверная стойка", "Almaty-Lab", "B-210", 27.0, 4.0, 30.0, "1.4.2"),
    ("dev-003", "Теплица", "Astana-Farm", "G-01", 22.0, 5.0, 35.0, "1.3.9"),
    ("dev-004", "Склад 1", "Astana-Farm", "W-01", 15.0, 2.0, 25.0, "1.3.9"),
    ("dev-005", "Офис, 3 этаж", "Almaty-Office", "O-305", 22.0, 1.5, 28.0, "1.4.2"),
    ("dev-006", "Серверная резервная", "Almaty-Office", "S-002", 26.0, 3.0, 32.0, "1.3.9"),
]


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_readings():
    rows = []
    for d_idx, dev in enumerate(DEVICES):
        dev_id, base, amp = dev[0], dev[4], dev[5]
        for i in range(24):
            noise = ((i * 7 + d_idx * 13) % 5 - 2) * 0.2
            temp = round(base + amp * math.sin(2 * math.pi * (i - 6) / 24) + noise, 1)
            hum = round(45 + 10 * math.sin(2 * math.pi * i / 24) + d_idx * 2, 1)
            batt = max(0, round(100 - i * 0.5 - d_idx * 2))
            rows.append({
                "device_id": dev_id,
                "ts": iso(DAY + timedelta(hours=i)),
                "temp_c": temp,
                "humidity_pct": hum,
                "battery_pct": batt,
            })
    return rows


def make_devices(readings):
    last = {}
    for r in readings:
        if r["device_id"] not in last or r["ts"] > last[r["device_id"]]["ts"]:
            last[r["device_id"]] = r
    out = []
    for dev_id, name, site, room, _b, _a, tmax, fw in DEVICES:
        lr = last[dev_id]
        out.append({
            "_id": dev_id,
            "name": name,
            "type": "env-sensor",
            "location": {"site": site, "room": room},
            "status": "active",
            "firmware": fw,
            "thresholds": {"temp_max": tmax},
            "last_reading": {
                "ts": lr["ts"],
                "temp_c": lr["temp_c"],
                "humidity_pct": lr["humidity_pct"],
                "battery_pct": lr["battery_pct"],
            },
        })
    return out


def make_events():
    def ev(dev, hour, minute, typ, sev, msg, ack):
        return {
            "device_id": dev,
            "ts": iso(DAY + timedelta(hours=hour, minutes=minute)),
            "type": typ,
            "severity": sev,
            "message": msg,
            "acknowledged": ack,
        }

    return [
        ev("dev-001", 1, 5, "info", "info", "Плановая калибровка выполнена", True),
        ev("dev-002", 2, 10, "info", "info", "Устройство перезапущено", True),
        ev("dev-004", 3, 30, "info", "info", "Обновление прошивки проверено", True),
        ev("dev-003", 5, 45, "info", "info", "Смена режима передачи", False),
        ev("dev-002", 11, 0, "high_temp", "warning", "Температура выше порога", False),
        ev("dev-002", 12, 0, "high_temp", "critical", "Температура значительно выше порога", False),
        ev("dev-006", 13, 15, "high_temp", "warning", "Температура близка к порогу", True),
        ev("dev-005", 15, 20, "low_battery", "warning", "Заряд батареи ниже 90%", False),
        ev("dev-004", 17, 40, "offline", "critical", "Нет данных более 30 минут", False),
        ev("dev-004", 18, 5, "online", "info", "Связь восстановлена", True),
        ev("dev-003", 20, 0, "high_temp", "warning", "Температура выше нормы", True),
        ev("dev-001", 22, 30, "info", "info", "Дверь камеры закрыта", False),
    ]


def js_value(v, indent=0):
    """Сериализация в литерал mongosh: строки ts превращаются в ISODate()."""
    pad = "  " * indent
    if isinstance(v, dict):
        if not v:
            return "{}"
        items = []
        for k, val in v.items():
            key = k if k.isidentifier() else json.dumps(k, ensure_ascii=False)
            if k == "ts":
                items.append(f'{pad}  {key}: ISODate("{val}")')
            else:
                items.append(f"{pad}  {key}: {js_value(val, indent + 1)}")
        return "{\n" + ",\n".join(items) + f"\n{pad}}}"
    if isinstance(v, bool):
        return "true" if v else "false"
    return json.dumps(v, ensure_ascii=False)


def compact(doc):
    """Однострочный литерал для коротких документов (readings)."""
    parts = []
    for k, v in doc.items():
        if k == "ts":
            parts.append(f'{k}: ISODate("{v}")')
        else:
            parts.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    return "{ " + ", ".join(parts) + " }"


def main():
    readings = make_readings()
    devices = make_devices(readings)
    events = make_events()

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "seed.json").write_text(
        json.dumps({"devices": devices, "readings": readings, "events": events},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    lines = [
        "// Лабораторная работа 8, вариант 6 (IoT-мониторинг). Тестовые данные.",
        "// Файл сгенерирован tools/generate_seed.py — не редактируйте вручную.",
        "// Запуск: mongosh --file scripts/02_seed.js",
        "db = db.getSiblingDB('lab8_iot');",
        "",
        "// Повторный запуск не должен дублировать данные: сначала очищаем только свои коллекции.",
        "db.devices.deleteMany({});",
        "db.readings.deleteMany({});",
        "db.events.deleteMany({});",
        "",
        "db.devices.insertMany([",
        ",\n".join("  " + js_value(d, 1) for d in devices),
        "]);",
        "",
        "db.readings.insertMany([",
        ",\n".join("  " + compact(r) for r in readings),
        "]);",
        "",
        "db.events.insertMany([",
        ",\n".join("  " + compact(e) for e in events),
        "]);",
        "",
        "print('devices: ' + db.devices.countDocuments());",
        "print('readings: ' + db.readings.countDocuments());",
        "print('events: ' + db.events.countDocuments());",
        "",
    ]
    (ROOT / "scripts").mkdir(exist_ok=True)
    (ROOT / "scripts" / "02_seed.js").write_text("\n".join(lines), encoding="utf-8")
    print(f"devices={len(devices)} readings={len(readings)} events={len(events)}")


if __name__ == "__main__":
    main()
