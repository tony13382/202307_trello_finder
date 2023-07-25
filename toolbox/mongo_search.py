# Import modules of MongoDB
from pymongo import MongoClient

import os
from dotenv import load_dotenv
load_dotenv()
mongodb_path = os.getenv("mongodb_path")

# 建立 MongoDB 連線
client = MongoClient(mongodb_path)
db = client.nthu_trello_helper
mongo_article_collection = db.article

def article_search(article_id):
    # 搜尋符合條件的文件
    query = {"link_id": article_id}
    result = mongo_article_collection.find_one(query)
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
