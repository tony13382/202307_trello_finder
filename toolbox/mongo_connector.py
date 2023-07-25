# Import modules of MongoDB
from pymongo import MongoClient
# Import modules of datetime(For Log)
from datetime import datetime
# Setup environment value
import os
from dotenv import load_dotenv
load_dotenv()
mongodb_path = os.getenv("mongodb_path")

# 建立 MongoDB 連線
client = MongoClient(mongodb_path)
db = client.nthu_trello_helper
mongo_article_collection = db.article
mongo_trello_log_collection = db.trello_log


####################
## 搜尋文章
# Request Value
# article_id : String (track_id)
#-------------------
# Response Value
# state : Boolean
# result : Dict
####################
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


####################
## 新增 Trello Log （紀錄）
# Request Value
# card_id : String (Trello Card ID)
# state : Boolean
# msg : String (Log Message)
# time : String (Log Time %Y-%m-%d %H:%M:%S ) 2023-07-25 12:53:41 [可選]
####################

def add_trello_log(card_id, state, msg, time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),more_info=""):
    # 插入 MongoDB
    mongo_trello_log_collection.insert_one({
        "datetime" : time,
        "card_id" : card_id,
        "state" : state,
        "msg" : msg,
        "more_info" : more_info,
    })
