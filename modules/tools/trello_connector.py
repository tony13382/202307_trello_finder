
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
    print("+----------------------------+")
    print("卡片下留言(純文字)成功")
    print("+----------------------------+")


####################
## 在卡片下留言(含圖片)
# Request Value
# card_id : String (Trello Card ID)
# img_path : String (圖片路徑-公網可見圖檔路徑)
# data : msgString (留言內容)
####################
def addCommentWithPictureToCard(card_id,img_path, msgString):
    send_msg = f"![songlaInpageCover.png]({img_path})\n\n {msgString}"
    addCommentToCard(card_id,send_msg)
    print("+----------------------------+")
    print("卡片下留言(含圖片)成功")
    print("+----------------------------+")


####################
#上傳檔案至卡片
# Request Value
# card_id : String (Trello Card ID)
# file_path : String (檔案路徑)
####################
def addFileToCard(card_id,file_path):
    # 上傳圖片，獲取附件ID
    url = f"https://api.trello.com/1/cards/{card_id}/attachments"
    params = {"key": api_key, "token": api_token}
    files = {"file": open(file_path, "rb")}
    response = requests.post(url, params=params, files=files)
    data = response.json()
    attachment_id = data["id"]
    print("Upload Done. ",attachment_id)
    return attachment_id

def addCoverToCard(card_id,img_path):
    # 上傳圖片，獲取附件ID
    attachment_id = addFileToCard(card_id,img_path)    
    
    # 將附件ID設置為封面
    url = f"https://api.trello.com/1/cards/{card_id}/idAttachmentCover"
    params = {"key": api_key, "token": api_token, "value": attachment_id}
    response = requests.put(url, params=params)
    print(response.json())

    print("+----------------------------+")
    print("封面設置成功")
    print("+----------------------------+")