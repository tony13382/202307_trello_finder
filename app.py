# coding:utf-8
####################################################################
### Flask Server 用於接收 Trello Webhook 訊息
####################################################################

# Flask 模組(用於建立 Web API Server)
from flask import Flask, render_template, request
# MongoDB 文章搜尋模組 (比對歷史資料確認是否有重複呼叫)
import modules.tools.mongo_connector as mongo_connector
# RabbitMQ 模組 （用於發送任務）
import modules.tools.rabbitmq_connector as rabbitmq_connector

####################################################################
# Setup environment value
####################################################################
import yaml
with open('config.yml', 'r', encoding='utf-8') as config_File:
    config = yaml.safe_load(config_File)
FLASK_SERVER_PORT = config['flask']['port']
####################################################################


####################################################################
# 啟動詞載入
####################################################################
import modules.tools.process_words as read_txt_to_list
action_word_list = read_txt_to_list.txt_to_list("./setting/action_word_list.txt")
print("啟動詞載入完成！")
####################################################################


####################################################################
# 自定義本頁Function
####################################################################
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
                # 確保資料結構有 [action][type] 這個屬性
                if req.get("action", {}).get("type") is not None:
                    # 輸出資料
                    print("偵測到 Trello Action",req["action"]["type"])
                    # 判斷是否為新增卡片
                    if(req["action"]["type"] == "createCard"):
                        print("偵測到新增卡片")
                        # 取得卡片名稱與 ID
                        user_input = req["action"]["data"]["card"]["name"]
                        card_id = req["action"]["data"]["card"]["id"]
                        # 檢查是否重複呼叫
                        if mongo_connector.check_has_record(card_id):
                            print("\033[0;31m 重複呼叫 停止執行. \033[0m\n")
                            print("====================")
                            return ("", 200)
                        # 檢查是否包含動作關鍵字
                        if(check_action_word(user_input,action_word_list)):
                            # 發送任務給 RabbitMQ
                            rabbitmq_connector.send_trello_mission(data={
                                'card_id': card_id,
                                'input_string': user_input,
                                'trello_req': req
                            })
                            return ("", 200)
                        else:
                            print("不包含動作關鍵字: ",user_input)
                            return ("", 200)
                    else:
                        return ("", 200)
                        
            except Exception as exp:
                print("\033[0;31m Cannot 偵測到新增卡片 \033[0m\n \n",exp)
        except:
            print("\033[0;31m Null Request, It may be a check request \033[0m\n")
            
    return ("", 200)


if __name__ == '__main__':
    # Set Debug Mode （每次儲存自動刷新，正式上線需要關閉）
    app.debug = True
    # Run Server on 0.0.0.0 （允許外部連線）
    app.run(host="0.0.0.0",port=FLASK_SERVER_PORT)