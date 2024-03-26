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
# Trello 模組 （用於修改）
import modules.tools.trello_connector as trello_connector
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
# Check Trello is Create Card and Contain Action Word
####################################################################
def checkIsSearchType(req):
    try:
        if req.get("action", {}).get("type") is not None:
            if(req["action"]["type"] == "createCard"):
                print("偵測到新增卡片")
                # 取得卡片名稱與 ID
                user_input = req["action"]["data"]["card"]["name"]
                card_id = req["action"]["data"]["card"]["id"]
                # 檢查是否重複呼叫
                if mongo_connector.check_has_record(card_id) is True:
                    print("\033[0;31m 重複呼叫 停止執行. \033[0m\n")
                    print("====================")
                    return False
                # 檢查是否包含動作關鍵字
                if(check_action_word(user_input,action_word_list)):
                    return True
                elif user_input[0:1] == "#":
                    return True
                else:
                    print("不包含動作關鍵字: ",user_input)
                    return False
            else:
                return False
        else:
            return False
    except Exception as exp:
        print("\033[0;31m 無法偵測到新增卡片 \033[0m\n \n",exp)
        return False
####################################################################


####################################################################
# Check Trello is Comment Action and Contain Trello Bot Tag
####################################################################
TRELLO_BOT_ID = config['trello']['id_of_trello_bot']
TRELLO_BOT_TAG = config['trello']['tag_of_trello_bot']
def checkIsCommentType(req):
    try:
        if req.get("action", {}).get("type") is not None:
            if(req["action"]["type"] == "commentCard"):
                print("偵測到留言")
                # 取得用戶 ID
                user_id = req["action"]["idMemberCreator"]
                # 取得留言內容
                user_input = req["action"]["data"]["text"]
                # 檢查格式 1. 留言包含特定文本 2. 留言者不是機器人
                if user_id != TRELLO_BOT_ID and TRELLO_BOT_TAG in user_input:
                    return True
                else:
                    print("留言者是機器人或不包含特定文本")
                    return False
    except Exception as exp:
        print("\033[0;31m 偵測留言錯誤 \033[0m\n \n",exp)
        return False
####################################################################


####################################################################
# API Server
####################################################################

# 圖床設定
app = Flask(__name__,static_url_path='/imgs',static_folder='static/images/')

# 首頁
@app.route('/',methods=['GET'])
def index():
    return render_template('index.html')

# Webhook 路由
@app.route('/webhook3',methods=['POST','HEAD','GET'])
def webhook_v3_post():
    if request.method == 'POST':
        try:
            # Get Request Data
            req = request.json
            try:
                # 確保資料結構有 [action][type] 這個屬性
                if checkIsSearchType(req) is True:
                    card_title = req["action"]["data"]["card"]["name"]
                    # 發送任務給 RabbitMQ
                    rabbitmq_connector.send_trello_mission(data={
                        'card_id': req["action"]["data"]["card"]["id"],
                        'input_string': req["action"]["data"]["card"]["name"],
                        'trello_req': req
                    })
                    card_id = req["action"]["data"]["card"]["id"]
                    # 更新卡片名稱
                    trello_connector.updateDataToCard(card_id, {
                        "name" : f"[正在等待] {card_title}",
                    })
                    return ("", 200)
                elif checkIsCommentType(req) is True:
                    print("偵測到留言")
                    user_id = req["action"]["idMemberCreator"]
                    card_id = req["action"]["data"]["card"]["id"]
                    user_input = req["action"]["data"]["text"]
                    print(f"{user_id}: {user_input}")
                    rabbitmq_connector.send_trello_discuess(data={
                        'card_id': card_id,
                        'input_string': user_input,
                        'trello_req': req
                    })
                    card_title = trello_connector.getCardTitle(card_id,filter=True)
                    trello_connector.updateDataToCard(card_id, {
                        "name" : f"[正在等待] {card_title}",
                    })
                else:
                    return ("", 200)
                        
            except Exception as exp:
                print("\033[0;31m 判斷核心錯誤 \033[0m\n \n",exp)
        except:
            print("\033[0;31m Null Request, It may be a check request \033[0m\n")
            
    return ("", 200)


if __name__ == '__main__':
    # Set Debug Mode （每次儲存自動刷新，正式上線需要關閉）
    app.debug = True
    # Run Server on 0.0.0.0 （允許外部連線）
    app.run(host="0.0.0.0",port=FLASK_SERVER_PORT)