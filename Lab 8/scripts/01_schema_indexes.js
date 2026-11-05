// Лабораторная работа 8, вариант 6 (IoT-мониторинг): коллекции, валидация и индексы.
// Запуск: mongosh --file scripts/01_schema_indexes.js
// Используется отдельная учебная база lab8_iot; рабочие базы не затрагиваются.
db = db.getSiblingDB('lab8_iot');

['devices', 'readings', 'events'].forEach((name) => db.getCollection(name).drop());

// devices: карточка устройства + денормализованное последнее показание (last_reading)
db.createCollection('devices', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['_id', 'name', 'location', 'status', 'thresholds'],
      properties: {
        _id: { bsonType: 'string' },
        name: { bsonType: 'string', minLength: 1 },
        status: { enum: ['active', 'maintenance', 'decommissioned'] },
        location: {
          bsonType: 'object',
          required: ['site', 'room'],
          properties: { site: { bsonType: 'string' }, room: { bsonType: 'string' } }
        },
        thresholds: {
          bsonType: 'object',
          required: ['temp_max'],
          properties: { temp_max: { bsonType: 'number' } }
        }
      }
    }
  }
});

// readings: один документ = одно показание (append-only поток)
db.createCollection('readings', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['device_id', 'ts', 'temp_c'],
      properties: {
        device_id: { bsonType: 'string' },
        ts: { bsonType: 'date' },
        temp_c: { bsonType: 'number' },
        humidity_pct: { bsonType: 'number', minimum: 0, maximum: 100 },
        battery_pct: { bsonType: 'number', minimum: 0, maximum: 100 }
      }
    }
  }
});

// events: тревоги и служебные события устройств
db.createCollection('events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['device_id', 'ts', 'type', 'severity', 'acknowledged'],
      properties: {
        device_id: { bsonType: 'string' },
        ts: { bsonType: 'date' },
        severity: { enum: ['info', 'warning', 'critical'] },
        acknowledged: { bsonType: 'bool' }
      }
    }
  }
});

// Индексы строятся под access patterns (см. отчёт):
db.readings.createIndex({ device_id: 1, ts: -1 });              // AP1, AP2: последнее и интервал по устройству
db.events.createIndex({ device_id: 1, ts: -1 });                // события устройства
db.events.createIndex({ severity: 1, acknowledged: 1, ts: -1 }); // AP5, AP7: открытые тревоги, очистка
db.devices.createIndex({ 'location.site': 1, status: 1 });      // AP3: устройства площадки

print('Коллекции: ' + db.getCollectionNames().join(', '));
['devices', 'readings', 'events'].forEach((name) => {
  print(name + ': ' + db.getCollection(name).getIndexes().map((i) => i.name).join(', '));
});
