# -*- coding: utf-8 -*-
# Trello 模組
import modules.tools.trello_connector as trello_connector
# 搜尋演算法模組
import modules.search_engine.search_engine as search_engine
# SBERT 編碼模組
import modules.tools.process_words as process_words
# MongoDB 文章搜尋模組
import modules.tools.mongo_connector as mongo_connector
# Answer Core 模組
import modules.tools.answer_core as answer_core
# 用於 MQ
import pika
import json

# 啟動詞與無資料罐頭訊息載入完成！
import modules.tools.process_words as read_txt_to_list
action_word_list = read_txt_to_list.txt_to_list("./setting/action_word_list.txt")

import os
from dotenv import load_dotenv
load_dotenv()
rabbitmq_host = os.getenv("rabbitmq_host")
rabbitmq_port = os.getenv("rabbitmq_port")
rabbitmq_username = os.getenv("rabbitmq_username")
rabbitmq_password = os.getenv("rabbitmq_password")


def trello_mission(card_id, input_string):
    return_data = {
        'card_id' : card_id,
        'input_string' : input_string,
    }

    # 渲染標題
    trello_connector.updateDataToCard(card_id, {
        "name" : f"[進行中] {input_string}",
    })

    query_string = input_string
    #Remove input_string in action_word_list
    for action_word in action_word_list:
        if action_word in query_string:
            query_string = query_string.replace(action_word, "")
    return_data["query_string"] = query_string
    
    # 進行搜尋
    return_data["tf"] = search_engine.tf(query_string)
    return_data["mix"] = search_engine.sbert_mix_tf(query_string, except_article_ids=[ x["article_id"] for x in return_data["tf"]["alist"]])
    return_data["sbert"] = search_engine.sbert(query_string, except_article_ids=([ x["article_id"] for x in return_data["tf"]["alist"]] + [ x["_id"] for x in return_data["mix"]["alist"]]))
    
    # 結果留言
    if return_data["sbert"]["state"] is True:
        trello_connector.addCommentToCard(
            card_id, 
            return_data["sbert"]["comment_msg"]
        )
    else:
        print(return_data["sbert"]["err_msg"])
        return{
            "state" : False,
            "err_msg" : return_data["sbert"]["err_msg"]
        }
    
    if return_data["mix"]["state"] is True:
        trello_connector.addCommentToCard(
            card_id, 
            return_data["mix"]["comment_msg"]
        )
    else:
        print(return_data["mix"]["err_msg"])
        return{
            "state" : False,
            "err_msg" : return_data["mix"]["err_msg"]
        }
    
    if return_data["tf"]["state"] is True:
        trello_connector.addCommentToCard(
            card_id, 
            return_data["tf"]["comment_msg"]
        )
    else:
        print(return_data["tf"]["err_msg"])
        return{
            "state" : False,
            "err_msg" : return_data["tf"]["err_msg"]
        }

    # Add Divider
    trello_connector.addCommentToCard(
        card_id, 
        "---"
    )

    # 文字雲上傳
    if(len(return_data["tf"]["alist"]) + len(return_data["mix"]["alist"]) + len(return_data["sbert"]) == 0):
        trello_connector.addCoverToCard(
            card_id,
            "./static/images/not_found.png"
        )
    else:
        # 產生文字雲
        wc_img_path = process_words.generate_wordcloud(return_data["tf"]["wc_string"] + " " + return_data["mix"]["wc_string"] + " " + return_data["sbert"]["wc_string"])
        if wc_img_path["state"] is True:
            # 更新封面
            print("WordCloud 圖片產生成功")
            trello_connector.addCoverToCard(
                card_id,
                wc_img_path["value"]
            )


        # 產生回應
        trello_connector.updateDataToCard(card_id, {
            "name" : f"[已完成] {input_string}",
        })

    print("搜索結束")

    # GPT-3 回答
    # 產生回應
    answer = answer_core.qa_by_gpt3(query_string)
    if answer["state"] is True:
        trello_connector.addCommentToCard(
            card_id, 
            f"**參考回答：**\n --- \n\n{answer['value']} \n --- \n此為 GPT-3.5 模型回答，僅供參考。"
        )

    return {
        "state" : True,
        "search_result" : return_data
    }


def save_data_to_db(trello_mission_rq):
    if trello_mission_rq["state"] is True:    
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
        mongo_connector.add_trello_log(
            card_id = trello_mission_rq['search_result']["card_id"], 
            state = False, 
            msg = "執行失敗\n" + str(trello_mission_rq["err_msg"]), 
            more_info= trello_mission_rq
        )
    

def callback(ch, method, properties, body):
    # 将收到的JSON字符串转换为Dict数据
    print(body)
    print('------------------')
    data_dict = json.loads(body)
    
    card_id = data_dict.get('card_id', '')
    input_string = data_dict.get('input_string', '')
    trello_req = data_dict.get('trello_req', {})
    print(f" [x] Sent data: {card_id} | {input_string}. ")
    # 執行 Trello 任務(包含搜尋、留言、封面更新)
    trello_mission_rq = trello_mission(card_id, input_string)
    trello_mission_rq['trello_req'] = trello_req
    
    # 儲存資料到資料庫
    save_data_to_db(trello_mission_rq)

    
    

# 连接到RabbitMQ服务器
credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
parameters = pika.ConnectionParameters(rabbitmq_host, rabbitmq_port, '/', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# 声明一个队列
channel.queue_declare(queue='trello_mission')

# 设置消息回调函数
channel.basic_consume(queue='trello_mission', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
