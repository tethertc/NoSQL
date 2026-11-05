// Лабораторная работа 8, вариант 6: проверка индексов и сравнение двух способов (EXPLAIN).
// Запуск (после 01 и 02): mongosh --file scripts/04_explain.js
db = db.getSiblingDB('lab8_iot');

const stats = (cursor) => {
  const s = cursor.explain('executionStats').executionStats;
  return {
    nReturned: s.nReturned,
    totalKeysExamined: s.totalKeysExamined,
    totalDocsExamined: s.totalDocsExamined
  };
};

const intervalQuery = {
  device_id: 'dev-003',
  ts: { $gte: ISODate('2026-11-01T06:00:00Z'), $lt: ISODate('2026-11-01T12:00:00Z') }
};

print('\n=== A. Интервал по устройству: с индексом и без ===');
print('С индексом {device_id:1, ts:-1}:');
printjson(stats(db.readings.find(intervalQuery)));
print('Без индекса (hint $natural, полный просмотр коллекции):');
printjson(stats(db.readings.find(intervalQuery).hint({ $natural: 1 })));

print('\n=== B. Последнее показание: два способа ===');
print('Способ 1 (основная модель): devices.findOne по _id, last_reading внутри документа:');
printjson(stats(db.devices.find({ _id: 'dev-003' })));
print('Способ 2 (альтернатива): readings, сортировка по ts desc, limit 1:');
printjson(stats(db.readings.find({ device_id: 'dev-003' }).sort({ ts: -1 }).limit(1)));
