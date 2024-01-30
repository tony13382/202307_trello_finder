# Import modules of MongoDB
from pymongo import MongoClient
# Import modules of datetime(For Log)
from datetime import datetime,timezone,timedelta
# Setup environment value
import os
from dotenv import load_dotenv
load_dotenv()
mongodb_path = os.getenv("mongodb_path")
mongodb_username = os.getenv("mongodb_username")  # 替換為你的用戶名
mongodb_password = os.getenv("mongodb_password")  # 替換為你的密碼

# 建立 MongoDB 連線
client = MongoClient(mongodb_path, username=mongodb_username, password=mongodb_password)
db = client.nthu_trello_helper
mongo_article_collection = db.article
mongo_trello_log_collection = db.trello_log
mongo_word_injection_collection = db.injection_list
mongo_keyword_collection = db.keyword
mongo_keyword_record_collection = db.keyword_record

####################################################################
# simple funtion (only search)
####################################################################

def find_keyword_id(word):
    # 搜尋關鍵字 ID
    result = mongo_keyword_collection.find_one({
        "preview_str": word
    })
    if result is not None:
        return result["link_id"]
    else:
        return None

def find_keyword_word(k_id):
    # 搜尋關鍵字 ID
    result = mongo_keyword_collection.find_one({
        "link_id": str(k_id)
    })
    if result is not None:
        return result["preview_str"]
    else:
        return None

def find_keyrecord_by_kw(key_id, limit=100):
    # 搜尋包含該關鍵字 ID 之文章
    query = {"keyword_id": key_id}
    # 搜尋符合條件的文件並依據分數排序（降冪）
    result = mongo_keyword_record_collection.find(query).sort("tf_value", -1).limit(limit)
    result_array = []
    for document in result:
        result_array.append(document)
    return result_array

def find_keyrecord_by_aid(article_id, limit=1000):
    # 搜尋包含該關鍵字 ID 之文章
    query = {'article_id': article_id}
    # 搜尋符合條件的文件
    result = mongo_keyword_record_collection.find(query).sort("tf_value", -1).limit(limit)
    result_array = []
    for document in result:
        result_array.append(document)
    return result_array

def find_article_info(article_id):
    # 利用 文章ID 搜尋文章
    query = {"link_id": article_id}
    result = mongo_article_collection.find_one(query)
    return result

def find_injection_value(word):
    # Key => Value
    query = {"key": word}
    result = mongo_word_injection_collection.find_one(query)
    
    if result is not None:
        return result["value"]
    else:
        return None
    

def convert_klistid_to_info(keyword_list):
    return [ find_keyword_word(k_id) for k_id in keyword_list ]



####################################################################
# fuzzy funtion (only search)
####################################################################
def find_injection_value_fuzzy(word):
    pattern = f".*{word}.*"
    query_muilt = {"value": {"$regex": pattern, "$options": "i"}}  # "i" for case-insensitive search
    # 搜尋符合條件的文件
    result_muilt = mongo_word_injection_collection.find(query_muilt)
    return result_muilt


####################################################################
# complex funtion (not only search but process data)
####################################################################

####################
## 搜尋相似文字
# Request Value
# word : String (word)
#-------------------
# Response Value
# state : Boolean
# result : String
####################
def process_injectionword(word):
    
    return_str = word
    
    result = find_injection_value(word)
    # 處理搜尋結果
    if result is not None:
        # 有找到: 回傳文字加上注入結果
        return_str = return_str + " : " + str(result) + "\n"
    else:
        # 沒找到: 回傳文字加上注入 contain 結果
        return_str = return_str + " : "
        # 原本文字
        return_str = return_str + word
        # Contain 包含文字搜尋
        result_muilt = find_injection_value_fuzzy(word)
        if result_muilt is not None and len(word) > 1:
            for item in result_muilt:
                return_str = return_str + " " + item["key"] 
        # 換行
        return_str = return_str + "\n"
    
    return return_str


def get_alist_by_kw(value_to_search):
    # Step 1: 在 keyword 中搜索 value = 文本 的 link_id
    kw_id = find_keyword_id(value_to_search)
    if kw_id is None:
        print("No keyword found")
        return []
    else:
        # 搜尋包含該關鍵字 ID 之文章
        article_list = find_keyrecord_by_kw(kw_id)
        if article_list is None or len(article_list) == 0:
            print("No article found")
            return []
        else:
            return article_list


def get_other_keyword_by_alist(article_list):
    # 使用聚合管道進行分組、總和計算和排序
    pipeline = [
        {"$match": {"article_id": {"$in": article_list}}},
        {"$group": {
            "_id": "$keyword_id",
            "total_tf_value": {"$sum": "$tf_value"}
        }},
        {"$sort": {"total_tf_value": -1}}
    ]

    return list(mongo_keyword_record_collection.aggregate(pipeline))


def get_alist_by_klist(keyword_list):
    # 使用聚合管道進行分組、總和計算和排序
    pipeline = [
        {"$match": {"keyword_id": {"$in": keyword_list}}},
        {"$group": {
            "_id": "$article_id",
            "total_tf_value": {"$sum": "$tf_value"}
        }},
        {"$sort": {"total_tf_value": -1}}
    ]
    return list(mongo_keyword_record_collection.aggregate(pipeline))


def check_has_record(card_id_to_check):
    try:
        matching_record = mongo_trello_log_collection.find_one({"card_id": card_id_to_check, "state": True})
        if matching_record:
            return True
        else:
            return False
    except:
        return False


####################################################################
# Insert Data To MongoDB
####################################################################

####################
## 新增 Trello Log （紀錄）
# Request Value
# card_id : String (Trello Card ID)
# state : Boolean
# msg : String (Log Message)
# time : String (Log Time %Y-%m-%d %H:%M:%S ) 2023-07-25 12:53:41 [可選]
####################

def add_trello_log(card_id, state, msg, time="",more_info=""):
    # 設定時間
    if(len(time) < 1):
        dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
        dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換時區 -> 東八區
        time = dt2.strftime("%Y-%m-%d %H:%M:%S") # 將時間轉換為 string
        #print(realtime) 
    # 插入 MongoDB
    mongo_trello_log_collection.insert_one({
        "datetime" : time,
        "card_id" : card_id,
        "state" : state,
        "msg" : msg,
        "more_info" : more_info,
    })

    # 備份資料點
    try:
        print("同步備份")
        backupClient = MongoClient("mongodb://100.90.12.119:27017/")
        backup_log_collection = backupClient.nthu_trello_helper.trello_log
        # 插入 MongoDB
        backup_log_collection.insert_one({
            "datetime" : time,
            "card_id" : card_id,
            "state" : state,
            "msg" : msg,
            "more_info" : more_info,
        })
        print("同步備份完成")
    except:
        print("mongo remote server has connect error.")
        print("please check tail vpn")