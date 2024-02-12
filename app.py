# coding:utf-8
import ast # 用於將字串轉換成串列
import re
# Flask 模組
from flask import Flask
from flask import render_template, jsonify, redirect
from flask import request
# MongoDB 文章搜尋模組
import modules.tools.mongo_connector as mongo_connector
# RabbitMQ 模組
import modules.tools.rabbitmq_connector as rabbitmq_connector
# 用於多執行緒
import threading


####################################################################
# Setup environment value
####################################################################
import yaml
with open('config.yml', 'r', encoding='utf-8') as config_File:
    config = yaml.safe_load(config_File)
FLASK_SERVER_PORT = config['flask']['port']


####################################################################
# 指定文字檔路徑
import modules.tools.process_words as read_txt_to_list
action_word_list = read_txt_to_list.txt_to_list("./setting/action_word_list.txt")
print("啟動詞與無資料罐頭訊息載入完成！")


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
                # Define to Check Trello Action
                if  "action" in req.keys():
                    if  "type" in req["action"].keys():
                        print("偵測到 Trello Action",req["action"]["type"])
                        if(req["action"]["type"] == "createCard"):
                            print("偵測到新增卡片")
                            # Get Need Data
                            user_input = req["action"]["data"]["card"]["name"]
                            card_id = req["action"]["data"]["card"]["id"]
                            if mongo_connector.check_has_record(card_id):
                                print("重複呼叫 停止執行")
                                print("====================")
                                return ("", 200)

                            # 檢查是否包含動作關鍵字
                            if(check_action_word(user_input,action_word_list)):
                                rabbitmq_connector.send_trello_mission(data={
                                    'card_id': card_id,
                                    'input_string': user_input,
                                    'trello_req': req
                                }, coreNum = 1)
                                # coreNum
                                return ("", 200)
                            else:
                                print("不包含動作關鍵字: ",user_input)
                                return ("", 200)
                        else:
                            return ("", 200)
                        
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
    app.run(host="0.0.0.0",port=FLASK_SERVER_PORT)