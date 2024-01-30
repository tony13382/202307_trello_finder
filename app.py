# coding:utf-8
import ast # 用於將字串轉換成串列
import re

from flask import Flask
from flask import render_template, jsonify, redirect
from flask import request

# 用於隨機抽取回應（無答案時）
import random

# 用於貯列
#import pika
import json

import threading

####################################################################
# Setup environment value
####################################################################


import os
from dotenv import load_dotenv
load_dotenv()
distance_filter = float(os.getenv("distance_filter"))
flask_server_port = int(os.getenv("flask_server_port"))
# Webhook API
trello_request_limit = int(os.getenv("trello_request_limit"))
# Get Environment Value
anthropic_setup = os.getenv("anthropic_setup") in ["True", "true", "1"]
openai_setup = os.getenv("openai_setup") in ["True", "true", "1"]
roBERTa_setup = os.getenv("roBERTa_setup") in ["True", "true", "1"]
bert_setup = os.getenv("bert_setup") in ["True", "true", "1"]

rabbitmq_host = os.getenv("rabbitmq_host")
rabbitmq_port = os.getenv("rabbitmq_port")
rabbitmq_username = os.getenv("rabbitmq_username")
rabbitmq_password = os.getenv("rabbitmq_password")


# 讀取文字檔並轉換成串列
def txt_to_list(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.readlines()
            content = [line.strip() for line in content]
        return content
    except FileNotFoundError:
        print("找不到指定的檔案。請檢查檔案路徑是否正確。", file_path)
        return []
    except Exception as e:
        print("讀取檔案時發生錯誤：", e)
        return []


# 指定文字檔路徑
import modules.tools.read_txt_to_list as read_txt_to_list
action_word_list = read_txt_to_list.txt_to_list("./setting/action_word_list.txt")
not_found_msg_list = read_txt_to_list.txt_to_list("./setting/not_found_msg_list.txt")
print("啟動詞與無資料罐頭訊息載入完成！")


####################################################################
# Process Module
####################################################################


# SBERT 編碼模組
from modules.tools.process_words import embedding_sentence, process_sentence, generate_wordcloud
import modules.tools.process_words as process_words
# Milvus 向量搜尋與運算模組
from modules.tools.vector_search import search_article_vector
import modules.tools.vector_search as vector_search
# MongoDB 文章搜尋模組
from modules.tools.mongo_connector import find_article_info, add_trello_log
import modules.tools.mongo_connector as mongo_connector
# GPT 回答模組
from modules.tools.answer_core import qa_by_anthropic, qa_by_openai, qa_by_RoBERTa, qa_by_bert
# Trello 模組
from modules.tools.trello_connector import updateDataToCard, addCommentToCard, addCommentWithPictureToCard, addCoverToCard
import modules.tools.trello_connector as trello_connector
# Vector 計算模組
import modules.tools.vector_calc as vector_calculation
# 搜尋演算法模組
import modules.search_engine.search_engine as search_engine

# RabbitMQ 模組
#import modules.tools.rabbitmq_connector as rabbitmq_connector



# 驗證文本是否包含動作關鍵字
def check_action_word(input_string, action_word_list):
    for action_word in action_word_list:
        if action_word in input_string:
            return True
    
    return False
# 驗證文本是否包含「已完成」關鍵字
def check_is_done(input_string):
    if "[已完成]" in input_string:
        return True
    else:
        return False

"""
TODO: MQ 
def send_message_to_queue(data_json):
    # 连接到RabbitMQ服务器
    credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
    parameters = pika.ConnectionParameters(rabbitmq_host, rabbitmq_port, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    #  建立隊列
    channel.queue_declare(queue='img_queue')
    channel.basic_publish(exchange='', routing_key='img_queue', body=data_json)
    connection.close()
"""

def webhook_v3_engine(user_input,card_id,checkIsTrello = False):
    
    # 定義需要留言的組件
    return_data = {}
    return_data["user_input"] = user_input
    return_data["card_id"] = card_id
    
    # 驗證文本是否包含動作關鍵字
    if check_action_word(user_input, action_word_list) is True and check_is_done(user_input) is False:
        # 文本包含動作關鍵字，進行搜尋
        # Update Card Title to show the process is start
        if checkIsTrello is True:
            trello_connector.updateDataToCard(card_id, {
                "name" : f"[進行中] {user_input}",
            })
        

        # 進行搜尋
        return_data["tf"] = search_engine.tf(user_input)
        if checkIsTrello is True and return_data["tf"]["state"] is True:
            trello_connector.addCommentToCard(
                card_id, 
                return_data["tf"]["comment_msg"]
            )
        else:
            print(return_data["tf"]["err_msg"])

        return_data["mix"] = search_engine.sbert_mix_tf(user_input, except_article_ids=[ x["article_id"] for x in return_data["tf"]["alist"]])
        if checkIsTrello is True and return_data["mix"]["state"] is True:
            trello_connector.addCommentToCard(
                card_id, 
                return_data["mix"]["comment_msg"]
            )
        else:
            print(return_data["mix"]["err_msg"])

        return_data["sbert"] = search_engine.sbert(user_input, except_article_ids=([ x["article_id"] for x in return_data["tf"]["alist"]] + [ x["_id"] for x in return_data["mix"]["alist"]]))
        if checkIsTrello is True and return_data["sbert"]["state"] is True:
            trello_connector.addCommentToCard(
                card_id, 
                return_data["sbert"]["comment_msg"]
            )
        else:
            print(return_data["sbert"]["err_msg"])

        # Add Divider
        if checkIsTrello is True:
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
            wc_img_path = process_words.generate_wordcloud(return_data["tf"]["wc_string"]) + " " + len(return_data["mix"]["wc_string"]) + " " + len(return_data["sbert"]["wc_string"])
            if(wc_img_path["state"]):
                # 印刷分隔線
                trello_connector.addCommentToCard(
                    card_id, 
                    "---"
                )
                # 更新封面
                print("WordCloud 圖片產生成功")
                trello_connector.addCoverToCard(
                    card_id,
                    wc_img_path["value"]
                )


            # 產生回應
            trello_connector.updateDataToCard(card_id, {
                "name" : f"[已完成] {user_input}",
            })

        print("搜索結束")

        print("=====================================")
        return return_data


####################################################################
# API Server
####################################################################

app = Flask(__name__,static_url_path='/imgs',static_folder='static/images/')

@app.route('/',methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/webhook3',methods=['POST','HEAD','GET'])
def webhook_v3_post():
    if request.method == 'POST':
        try:
            # Get Request Data
            req = request.json
            try:
                run_system = False
                
                # Define to Check Trello Action
                if  "action" in req.keys():
                    if  "type" in req["action"].keys():
                        check_trello_action = True
                        print("偵測到 Trello Action",req["action"]["type"])
                        if(req["action"]["type"] == "createCard"):
                            print("偵測到新增卡片")
                            run_system = True
                    else:
                        check_trello_action = False
                        if req["action"] == "api":
                            print("偵測到新調試指令")
                            run_system = True

                if(run_system):
                    
                    if(check_trello_action):
                        user_input = req["action"]["data"]["card"]["name"]
                        card_id = req["action"]["data"]["card"]["id"]
                        #board_id = req["action"]["data"]["board"]["id"]
                    else:
                        user_input = req["user_input"]
                        card_id = req["card_id"]
                    
                    if mongo_connector.check_has_record(card_id):
                        print("重複呼叫 停止執行")
                        print("====================")
                        return ("", 200)

                    # 檢查是否包含動作關鍵字
                    if(check_action_word(user_input,action_word_list)):
                        try:
                            result_of_search = webhook_v3_engine(user_input,card_id,check_trello_action)
                            result_of_search["trello_data"] = req
                            mongo_connector.add_trello_log(
                                card_id = card_id, 
                                state = True, 
                                msg = "留言成功", 
                                more_info=result_of_search
                            )
                            if check_trello_action is True:
                                try:
                                    card_link = f"https://trello.com/c/{req['action']['data']['card']['shortLink']}"
                                    creator_id = req["action"]["display"]["entities"]["memberCreator"]["id"]
                                    creator_name = req["action"]["display"]["entities"]["memberCreator"]["text"]
                                    print(card_id,":",card_link,"by", creator_id,"[", creator_name,"]")
                                    # Save to MySQL
                                    
                                except Exception as exp:
                                    print("\033[91m Save to MySQL Error. \033[00m")
                                    print(exp)
                                    print("=====================================")
                            return ("", 200)
                        except Exception as exp:
                            mongo_connector.add_trello_log(
                                card_id = card_id, 
                                state = False, 
                                msg = "v3_engine Error" + "\n\n" + str(exp),
                                more_info = {
                                    "trello_data" :  req
                                }
                            )
                            return ("", 200)
                    else:
                        print("不包含動作關鍵字: ",user_input)
            except Exception as exp:
                print("Cannot 偵測到新增卡片\n",exp)
                pass
        except:
            print("null Request, It may be a check request")

    return ("", 200)


if __name__ == '__main__':
    # Set Debug Mode （每次儲存自動刷新，正式上線需要關閉）
    app.debug = True
    # Run Server on 0.0.0.0 （允許外部連線）
    app.run(host="0.0.0.0",port=flask_server_port)