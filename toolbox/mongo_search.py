from pymongo import MongoClient

# 建立 MongoDB 連線
client = MongoClient("mongodb://100.90.12.119:27017/")
db = client.nthu_trello_helper
mongo_collection = db.article

def article_search(article_id):
    # 搜尋符合條件的文件
    query = {"link_id": article_id}
    result = mongo_collection.find_one(query)
    # 處理搜尋結果
    if result:
        return {
            "state" : True,
            "value" : result,
        }
    else:
        return {
            "state" : False,
            "value" : "未找到符合條件的文件。" + str(article_id),
        }
