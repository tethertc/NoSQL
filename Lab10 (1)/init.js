// Переключаемся на базу данных по Варианту 9
const dbName = "social_network";
const dbNode = db.getSiblingDB(dbName);

// Записываем 20 постов
dbNode.posts.insertMany([
  {_id:1, author:"user1", text:"Пост 1"}, {_id:2, author:"user2", text:"Пост 2"},
  {_id:3, author:"user3", text:"Пост 3"}, {_id:4, author:"user1", text:"Пост 4"},
  {_id:5, author:"user4", text:"Пост 5"}, {_id:6, author:"user2", text:"Пост 6"},
  {_id:7, author:"user3", text:"Пост 7"}, {_id:8, author:"user5", text:"Пост 8"},
  {_id:9, author:"user1", text:"Пост 9"}, {_id:10, author:"user2", text:"Пост 10"},
  {_id:11, author:"user3", text:"Пост 11"}, {_id:12, author:"user4", text:"Пост 12"},
  {_id:13, author:"user5", text:"Пост 13"}, {_id:14, author:"user1", text:"Пост 14"},
  {_id:15, author:"user2", text:"Пост 15"}, {_id:16, author:"user3", text:"Пост 16"},
  {_id:17, author:"user4", text:"Пост 17"}, {_id:18, author:"user5", text:"Пост 18"},
  {_id:19, author:"user1", text:"Пост 19"}, {_id:20, author:"user2", text:"Пост 20"}
], {writeConcern: {w: "majority"}});

print("Успех! Всего постов в базе данных:", dbNode.posts.countDocuments());
