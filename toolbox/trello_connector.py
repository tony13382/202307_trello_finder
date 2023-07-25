
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
import json
import os
from dotenv import load_dotenv

# Setup Trello API Key and Token
load_dotenv()
api_key = os.getenv("trello_api_key")
api_token = os.getenv("trello_api_token")


####################
## 更新 Trello 卡片資料
# Request Value
# card_id : String (Trello Card ID)
# data : Dict (Trello Card Data)
# 常用參數
# name : String (卡片名稱)
# desc : String (卡片描述)
####################
def updateDataToCard(card_id,data):
    # https://developer.atlassian.com/cloud/trello/rest/api-group-cards/#api-cards-id-put
    
    # 初始設置
    url = f"https://api.trello.com/1/cards/{card_id}"
    headers = {"Accept": "application/json"}
    query = {
        'key': api_key,
        'token': api_token
    }
    query.update(data)

    response = requests.request(
        "PUT",
        url,
        headers=headers,
        params=query
    )
    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))


####################
## 在卡片下留言
# Request Value
# card_id : String (Trello Card ID)
# data : msgString (留言內容)
####################
def addCommentToCard(card_id,msgString):
    #https://developer.atlassian.com/cloud/trello/rest/api-group-cards/#api-cards-id-actions-comments-post
    # 初始設置
    url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
    headers = {
        "Accept": "application/json"
    }
    query = {
        'text': str(msgString),
        'key': api_key,
        'token': api_token
    }

    response = requests.request(
        "POST",
        url,
        headers=headers,
        params=query
    )
    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

def addCommentWithPictureToCard(card_id,img_path, msgString):
    send_msg = f"![songlaInpageCover.png]({img_path})\n {msgString}"
    addCommentToCard(card_id,send_msg)