# -*- coding: utf-8 -*-
####################################################################
### 用於接收 RabbitMQ 訊息，並進行 Trello 任務
####################################################################

# Trello 模組 (用於留言、更新封面)
import modules.tools.trello_connector as trello_connector
# 搜尋演算法模組 (TF, SBERT, Mix)
import modules.search_engine.search_engine as search_engine
# 文本處理模組 (引入文件、文字雲生成)
import modules.tools.process_words as process_words
# MongoDB （用於儲存任務執行記錄）
import modules.tools.mongo_connector as mongo_connector
# Answer Core 模組 (用於 GPT-3.5 回答)
import modules.tools.answer_core as ai_core
# 用於 rabbitMQ （接收訊息）
import pika
import json
# 用於刪除文字雲圖片
import os

# 啟動詞與載入完成！
import modules.tools.process_words as read_txt_to_list
action_word_list = read_txt_to_list.txt_to_list("./setting/action_word_list.txt")

####################################################################
# 設定 RabbitMQ 連線資訊
####################################################################
import yaml
with open('config.yml', 'r', encoding='utf-8') as config_File:
    config = yaml.safe_load(config_File)
RABBITMQ_HOST = config['rabbitMQ']['host']
RABBITMQ_PORT = config['rabbitMQ']['port']
RABBITMQ_USERNAME = config['rabbitMQ']['username']
RABBITMQ_PASSWORD = config['rabbitMQ']['password']
RABBITMQ_SEARCH_QUEUE = config['rabbitMQ']['search_queue']
####################################################################


####################################################################
# Trello 任務 (搜尋、留言、封面更新)
####################################################################
def trello_mission(card_id, input_string):
    input_string = input_string.replace("[正在等待] ", "")
    # 初始化回傳資料
    return_data = {
        'card_id' : card_id,
        'input_string' : input_string,
    }
    # 渲染標題（進行中）
    trello_connector.updateDataToCard(card_id, {
        "name" : f"[進行中] {input_string}",
    })
    #===========================
    # 設定索引文字
    query_string = input_string
    #===========================
    # 進行文字處理( AI 取得關鍵字)
    query_string = ai_core.get_keyword(query_string)
    # 移除動作詞
    for action_word in action_word_list:
        if action_word in query_string:
            query_string = query_string.replace(action_word, "")
    return_data["query_string"] = query_string
    #===========================
    # 進行搜尋
    # 初始化排除文章 ID
    except_article_ids = []
    # 透過 TF 演算法進行搜尋
    return_data["tf"] = search_engine.tf(query_string)
    # 如果 TF 搜尋成功，則將搜尋結果的文章 ID 加入排除清單
    if return_data["tf"].get("state", False) is True:
        except_article_ids = [ x["article_id"] for x in return_data["tf"]["alist"]]
    # 透過 Mix 演算法進行搜尋
    return_data["mix"] = search_engine.sbert_mix_tf(query_string, except_article_ids = except_article_ids)
    # 如果 Mix 搜尋成功，則將搜尋結果的文章 ID 加入排除清單
    if return_data["mix"].get("state", False) is True:
        except_article_ids = except_article_ids + [ x["_id"] for x in return_data["mix"]["alist"]]
    # 透過 SBERT 演算法進行搜尋
    return_data["sbert"] = search_engine.sbert(query_string, except_article_ids=except_article_ids)
    #===========================
    # 根據結果進行留言
    # 從 SBERT -> Mix -> TF 倒序留言，以便於使用者看到最接近的結果在最上方
    if return_data["sbert"].get("state", False) is True:
        trello_connector.addCommentToCard(
            card_id, 
            return_data["sbert"]["comment_msg"]
        )
    else:
        print(return_data["sbert"]["err_msg"])
        return {
            "state" : False,
            "err_msg" : return_data["sbert"]["err_msg"],
            'card_id' : card_id,
            'input_string' : input_string,
        }
    if return_data["mix"].get("state", False) is True:
        trello_connector.addCommentToCard(
            card_id, 
            return_data["mix"]["comment_msg"]
        )
    else:
        print(return_data["mix"]["err_msg"])
        return{
            "state" : False,
            "err_msg" : return_data["mix"]["err_msg"],
            'card_id' : card_id,
            'input_string' : input_string,
        }
    if return_data["tf"].get("state", False) is True:
        trello_connector.addCommentToCard(
            card_id, 
            return_data["tf"]["comment_msg"]
        )
    else:
        print(return_data["tf"]["err_msg"])
        return{
            "state" : False,
            "err_msg" : return_data["tf"]["err_msg"],
            'card_id' : card_id,
            'input_string' : input_string,
        }

    # 新增分隔線
    trello_connector.addCommentToCard(
        card_id, 
        "---"
    )
    # 文字雲上傳
    # 如果搜尋結果為空，則上傳 not_found.png
    if(len(return_data["tf"]["alist"]) + len(return_data["mix"]["alist"]) + len(return_data["sbert"]) == 0):
        trello_connector.addCoverToCard(
            card_id = card_id,
            img_path = "static/images/not_found.png"
        )
    else:
        # 根據回應文字雲文字產生文字雲（tf 權重 3、mix 權重 2、sbert 權重 1）
        wc_img_path = process_words.generate_wordcloud(
            input_string= ( return_data["tf"]["wc_string"] + " " ) *3 + ( return_data["mix"]["wc_string"] + " " ) *2 + return_data["sbert"]["wc_string"],
            filename=card_id
        )
        # 如果文字雲產生成功，則上傳文字雲
        if wc_img_path["state"] is True:
            # 更新封面
            print("WordCloud 圖片產生成功")
            trello_connector.addCoverToCard(
                card_id,
                wc_img_path["value"]
            )
            # 上傳完成，刪除圖片
            os.remove(wc_img_path["value"])

        # 刷新卡片標題（已完成）
        trello_connector.updateDataToCard(card_id, {
            "name" : f"[已完成] {input_string}",
        })
    print("搜索結束")
    # 回傳執行成功資料
    return {
        "state" : True,
        "search_result" : return_data
    }
####################################################################


####################################################################
# 儲存資料到資料庫 MongoDB
####################################################################
def save_data_to_db(trello_mission_rq):
    if trello_mission_rq["state"] is True:    
        # 執行成功，儲存資料
        mongo_connector.add_trello_log(
            card_id = trello_mission_rq['search_result']["card_id"], 
            state = True, 
            msg = "留言成功", 
            more_info= {
                "card_id" : trello_mission_rq['search_result']["card_id"],
                "user_input" : trello_mission_rq['search_result']["input_string"],
                "tf": trello_mission_rq['search_result']["tf"],
                "mix": trello_mission_rq['search_result']["mix"],
                "sbert": trello_mission_rq['search_result']["sbert"],
                "trello_data" : trello_mission_rq['trello_req'],
            }
        )
    else:
        # 執行失敗，儲存錯誤資料
        mongo_connector.add_trello_log(
            card_id = trello_mission_rq['search_result']["card_id"], 
            state = False, 
            msg = "執行失敗\n" + str(trello_mission_rq["err_msg"]), 
            more_info= trello_mission_rq
        )
####################################################################
        
    
####################################################################
# RabbitMQ 訊息接收
####################################################################
def callback(ch, method, properties, body):
    #===========================
    # 整理資料轉換成變數
    # 将收到的JSON字符串转换为Dict数据
    data_dict = json.loads(body)
    # 整理資料成常用變數
    card_id = data_dict.get('card_id', '')
    input_string = data_dict.get('input_string', '')
    trello_req = data_dict.get('trello_req', {})
    #===========================
    print(f" [x] Sent data: {card_id} | {input_string}. ")
    # 執行 Trello 任務(包含搜尋、留言、封面更新)
    if card_id != "" and input_string != "":
        # 執行任務
        trello_mission_rq = trello_mission(card_id, input_string)
        # 任務資料儲存與附加行為資訊
        trello_mission_rq['trello_req'] = trello_req
        # 儲存資料到資料庫
        save_data_to_db(trello_mission_rq)
    else:
        # 如果資料為空，則回傳錯誤
        print("\033[0;31m Get Null Data. Please Check Again. \033[0m\n")
####################################################################
    
    
####################################################################
# 连接到RabbitMQ服务器
####################################################################
credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
parameters = pika.ConnectionParameters(
    host= RABBITMQ_HOST,
    port=RABBITMQ_PORT,
    virtual_host='/',
    credentials=credentials,
    heartbeat = 180  # 設定心跳間隔為 180 秒 / 3mins
)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
# 声明一个队列
channel.queue_declare(queue = RABBITMQ_SEARCH_QUEUE)
# 设置消息回调函数
channel.basic_consume(queue = RABBITMQ_SEARCH_QUEUE, on_message_callback=callback, auto_ack=True)
print(f' [*] Q:{RABBITMQ_SEARCH_QUEUE}| Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
####################################################################