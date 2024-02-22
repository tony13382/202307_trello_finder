
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
TRELLO_BOT_ID = config['trello']['id_of_trello_bot']
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
    #print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    print("+----------------------------+")
    print("卡片資料更新成功",response.status_code)
    print(f"Card_id: {card_id}\nData: {data}")
    print("+----------------------------+")
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
    #print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    print("+----------------------------+")
    print("卡片下留言(純文字)成功",response.status_code)
    print("CardID:", card_id, "Msg:", msgString)
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
    # 輸出結果
    print("Add File To Card Done. ", response.status_code)
    print("Upload Done. ID:",attachment_id)
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
    print("封面設置成功",response.status_code)
    print("+----------------------------+")
####################################################################
    

####################################################################
# 取得卡片留言
# Request Value:
# card_id : String (Trello Card ID)
####################################################################
def getCommentsFromCard(card_id, filter = True):
    # API 連結設定
    print(f"Card_id: {card_id}")
    url = f"https://api.trello.com/1/cards/{card_id}/actions"
    # 設定標頭
    headers = { "Accept": "application/json" }
    # 設定查詢參數
    query = {
        'filter': 'commentCard',
        'key': TRELLO_API_KEY,
        'token': TRELLO_API_TOKEN
    }
    # 發送請求
    response = requests.request(
        method = "GET",
        url = url,
        headers=headers,
        params=query
    )
    # 設定留言清單
    comments_list = []
    # request 結果轉換成 list
    if response.status_code == 200:
        req_objects = json.loads(response.text)
        for req_object in req_objects:
            create_id = req_object.get("idMemberCreator",None)
            # 如果沒有留言者 ID 則跳過
            if create_id is None:
                continue
            # 篩除由系統自動產生的留言
            elif filter is True and create_id == TRELLO_BOT_ID:
                continue
            else:
                comments_list.append({
                    "create_id": create_id,
                    "comment_str": req_object.get("data",{}).get("text","")
                })
    # 輸出結果
    return comments_list
####################################################################


####################################################################
# 取得卡片標題
# Request Value:
# card_id : String (Trello Card ID)
####################################################################
def getCardTitle(card_id):
    # API 連結設定
    url = f"https://api.trello.com/1/cards/{card_id}"
    # 設定標頭
    headers = { "Accept": "application/json" }
    # 設定查詢參數
    query = {
        'key': TRELLO_API_KEY,
        'token': TRELLO_API_TOKEN
    }
    # 發送請求
    response = requests.request(
        method = "GET",
        url = url,
        headers=headers,
        params=query
    )
    # 輸出結果
    return json.loads(response.text).get("name","")
####################################################################