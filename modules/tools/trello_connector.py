
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
import json

####################################################################
# Setup Trello API Key and Token
####################################################################
import yaml
with open('config.yml', 'r', encoding='utf-8') as config_File:
    config = yaml.safe_load(config_File)
TRELLO_API_KEY = config['trello']['api_key']
TRELLO_API_TOKEN = config['trello']['token']

####################################################################


####################################################################
## 更新 Trello 卡片資料
# Request Value
# card_id : String (Trello Card ID)
# data : Dict (Trello Card Data)
# 常用參數
# name : String (卡片名稱)
# desc : String (卡片描述)
####################################################################
def updateDataToCard(card_id,data):
    # 參考資料： https://developer.atlassian.com/cloud/trello/rest/api-group-cards/#api-cards-id-put
    # 初始設置
    url = f"https://api.trello.com/1/cards/{card_id}"
    headers = {"Accept": "application/json"}
    query = {
        'key': TRELLO_API_KEY,
        'token': TRELLO_API_TOKEN
    }
    query.update(data)
    # 發送請求
    response = requests.request(
        "PUT",
        url,
        headers=headers,
        params=query
    )
    # 輸出結果
    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
####################################################################


####################################################################
## 在卡片下留言
# Request Value
# card_id : String (Trello Card ID)
# data : msgString (留言內容)
####################################################################
def addCommentToCard(card_id,msgString):
    # 參考資料： https://developer.atlassian.com/cloud/trello/rest/api-group-cards/#api-cards-id-actions-comments-post
    # 初始設置
    url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
    headers = {
        "Accept": "application/json"
    }
    query = {
        'text': str(msgString),
        'key': TRELLO_API_KEY,
        'token': TRELLO_API_TOKEN
    }
    # 發送請求
    response = requests.request(
        "POST",
        url,
        headers=headers,
        params=query
    )
    # 輸出結果
    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    print("+----------------------------+")
    print("卡片下留言(純文字)成功")
    print("+----------------------------+")
####################################################################


####################################################################
# 上傳檔案至卡片
# Request Value
# card_id : String (Trello Card ID)
# file_path : String (檔案路徑)
####################################################################
def addFileToCard(card_id,file_path):
    # 上傳圖片，獲取附件ID
    url = f"https://api.trello.com/1/cards/{card_id}/attachments"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_API_TOKEN}
    files = {"file": open(file_path, "rb")}
    response = requests.post(url, params=params, files=files)
    data = response.json()
    attachment_id = data["id"]
    print("Upload Done. ",attachment_id)
    return attachment_id
####################################################################


####################################################################
# 將圖片檔案路徑設置為封面
# Request Value:
# card_id : String (Trello Card ID)
# img_path : String (圖片檔案路徑)
####################################################################
def addCoverToCard(card_id,img_path):
    # 上傳圖片，獲取附件ID
    attachment_id = addFileToCard(card_id,img_path)        
    # 將附件ID設置為封面
    url = f"https://api.trello.com/1/cards/{card_id}/idAttachmentCover"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_API_TOKEN, "value": attachment_id}
    response = requests.put(url, params=params)
    #print(response.json())
    # 輸出結果
    print("+----------------------------+")
    print("封面設置成功")
    print("+----------------------------+")
####################################################################