### 搜尋紀錄 Log 以日期到序排列
``` nodejs
db.getCollection("trello_log").find({}).sort({"datetime":-1})
```
### 搜尋注入表
``` nodejs
db.getCollection("injection_list").find({"value":{$regex:"關鍵字"}})
```
### 以關鍵字篩查搜尋文章
``` nodejs
db.getCollection("article").find({"title": {$regex:"關鍵字"}})
```

``` nodejs
db.getCollection("article").find({"content": {$regex:"關鍵字"}})
```