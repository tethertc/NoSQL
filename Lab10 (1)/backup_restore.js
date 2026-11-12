// Скрипт симуляции бэкапа и восстановления данных в изолированную БД
// Подключаться к выжившему порту 27102 после падения primary

const sourceDB = db.getSiblingDB("social_network");
const targetDB = db.getSiblingDB("social_network_restore");

print("Запуск резервного копирования коллекции posts...");

// Копирование данных через агрегацию (симуляция бэкапа в изолированную среду)
sourceDB.posts.aggregate([
  { $out: { db: "social_network_restore", coll: "posts" } }
]);

print("Восстановление завершено успешно!");
print("Количество проверочных документов в новой БД:", targetDB.posts.countDocuments());
