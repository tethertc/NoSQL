// Лабораторная работа 8, вариант 6 (IoT-мониторинг): ключевые запросы.
// Запуск (после 01 и 02): mongosh --file scripts/03_queries.js
// Скрипт изменяет данные (Q4, Q5, Q8, Q9): для повторного прогона заново выполните 02_seed.js.
db = db.getSiblingDB('lab8_iot');

const show = (title, value) => {
  print('\n=== ' + title + ' ===');
  printjson(value);
};

// ---------------------------------------------------------------- Q1 (чтение)
// AP1. Последнее показание устройства: один документ по _id, без сортировки.
show('Q1. Последнее показание dev-001',
  db.devices.findOne({ _id: 'dev-001' }, { name: 1, last_reading: 1 }));

// ---------------------------------------------------------------- Q2 (чтение)
// AP2. Показания устройства за интервал [06:00; 12:00): индекс {device_id, ts}.
show('Q2. Показания dev-003 за 06:00-12:00',
  db.readings.find(
    {
      device_id: 'dev-003',
      ts: { $gte: ISODate('2026-11-01T06:00:00Z'), $lt: ISODate('2026-11-01T12:00:00Z') }
    },
    { _id: 0, ts: 1, temp_c: 1 }
  ).sort({ ts: 1 }).toArray());

// ---------------------------------------------------------------- Q3 (чтение)
// AP3. Активные устройства площадки: индекс {location.site, status}.
show('Q3. Активные устройства площадки Almaty-Lab',
  db.devices.find(
    { 'location.site': 'Almaty-Lab', status: 'active' },
    { name: 1, 'location.room': 1, firmware: 1 }
  ).toArray());

// ---------------------------------------------------------------- Q4 (запись события)
// AP4. Запись события о превышении порога.
show('Q4. Запись события high_temp для dev-002',
  db.events.insertOne({
    device_id: 'dev-002',
    ts: ISODate('2026-11-02T00:00:00Z'),
    type: 'high_temp',
    severity: 'critical',
    message: 'Температура выше порога 30 °C',
    acknowledged: false
  }));

// ---------------------------------------------------------------- Q5 (изменение)
// AP5. Новое показание + обновление last_reading. Условие last_reading.ts < ts
// не даёт запоздавшему показанию затереть более свежее.
const newReading = {
  device_id: 'dev-002',
  ts: ISODate('2026-11-02T00:00:00Z'),
  temp_c: 31.4,
  humidity_pct: 44.0,
  battery_pct: 87
};
db.readings.insertOne(newReading);
show('Q5. Обновление last_reading dev-002',
  db.devices.updateOne(
    { _id: 'dev-002', 'last_reading.ts': { $lt: newReading.ts } },
    {
      $set: {
        last_reading: {
          ts: newReading.ts,
          temp_c: newReading.temp_c,
          humidity_pct: newReading.humidity_pct,
          battery_pct: newReading.battery_pct
        }
      }
    }
  ));
show('Q5 (проверка). dev-002 после обновления',
  db.devices.findOne({ _id: 'dev-002' }, { name: 1, last_reading: 1 }));

// ---------------------------------------------------------------- Q6 (аналитика)
// AP6. Статистика температуры по устройствам за сутки 2026-11-01 и сравнение с порогом.
show('Q6. Статистика за 2026-11-01 по устройствам',
  db.readings.aggregate([
    {
      $match: {
        ts: { $gte: ISODate('2026-11-01T00:00:00Z'), $lt: ISODate('2026-11-02T00:00:00Z') }
      }
    },
    {
      $group: {
        _id: '$device_id',
        n: { $sum: 1 },
        avg_temp: { $avg: '$temp_c' },
        min_temp: { $min: '$temp_c' },
        max_temp: { $max: '$temp_c' }
      }
    },
    { $lookup: { from: 'devices', localField: '_id', foreignField: '_id', as: 'dev' } },
    { $unwind: '$dev' },
    {
      $project: {
        _id: 1,
        n: 1,
        avg_temp: { $round: ['$avg_temp', 2] },
        min_temp: 1,
        max_temp: 1,
        temp_max_threshold: '$dev.thresholds.temp_max',
        over_threshold: { $gt: ['$max_temp', '$dev.thresholds.temp_max'] }
      }
    },
    { $sort: { max_temp: -1 } }
  ]).toArray());

// ---------------------------------------------------------------- Q7 (аналитика)
// AP7. Сколько неподтверждённых событий каждого уровня важности.
show('Q7. Неподтверждённые события по уровням важности',
  db.events.aggregate([
    { $match: { acknowledged: false } },
    { $group: { _id: '$severity', n: { $sum: 1 } } },
    { $sort: { n: -1, _id: 1 } }
  ]).toArray());

// ---------------------------------------------------------------- Q8 (безопасное удаление)
// AP8. Очистка: подтверждённые info-события старше 06:00. Сначала контрольная
// выборка и подсчёт по тому же фильтру, и только затем deleteMany.
const cleanupFilter = {
  severity: 'info',
  acknowledged: true,
  ts: { $lt: ISODate('2026-11-01T06:00:00Z') }
};
show('Q8a. Контрольная выборка перед удалением',
  db.events.find(cleanupFilter, { _id: 0, device_id: 1, ts: 1, message: 1 }).sort({ ts: 1 }).toArray());
const toDelete = db.events.countDocuments(cleanupFilter);
print('К удалению: ' + toDelete);
if (toDelete > 0 && toDelete <= 10) {
  show('Q8b. Результат удаления', db.events.deleteMany(cleanupFilter));
} else {
  print('Удаление отменено: число документов вне ожидаемого диапазона.');
}
print('Событий осталось: ' + db.events.countDocuments());

// ---------------------------------------------------------------- Q9 (инвалидирование)
// AP9. Вывод устройства из эксплуатации без удаления истории (мягкое инвалидирование).
show('Q9. Вывод dev-006 из эксплуатации',
  db.devices.updateOne({ _id: 'dev-006' }, { $set: { status: 'decommissioned' } }));
show('Q9 (проверка). Устройства по статусам',
  db.devices.aggregate([
    { $group: { _id: '$status', n: { $sum: 1 } } },
    { $sort: { _id: 1 } }
  ]).toArray());
