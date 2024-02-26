# -*- coding: utf-8 -*-
####################################################################
### 用於接收 RabbitMQ 訊息，並進行 Trello 任務
####################################################################

# Trello 模組 (用於留言、更新封面)
import modules.tools.trello_connector as trello_connector
# MongoDB （用於儲存任務執行記錄）
import modules.tools.mongo_connector as mongo_connector
# GPT-3.5 模組 (用於回答)
import modules.tools.answer_core as answer_core
# 用於 rabbitMQ （接收訊息）
import pika
import json


####################################################################
# 設定 RabbitMQ 連線資訊
####################################################################
import yaml
with open('config.yml', 'r', encoding='utf-8') as config_File:
    config = yaml.safe_load(config_File)
# ---------------------------------------------------------------
RABBITMQ_HOST = config['rabbitMQ']['host']
RABBITMQ_PORT = config['rabbitMQ']['port']
RABBITMQ_USERNAME = config['rabbitMQ']['username']
RABBITMQ_PASSWORD = config['rabbitMQ']['password']
RABBITMQ_COMMENT_QUEUE = config['rabbitMQ']['comment_queue']
# ---------------------------------------------------------------
TRELLO_BOT_ID = config['trello']['id_of_trello_bot']
TRELLO_BOT_TAG = config['trello']['tag_of_trello_bot']
# ---------------------------------------------------------------
FOOTER_OF_BOT_REQ = "\n\n---\n以上內容僅供參考，如有任何問題，請隨時聯絡我們。"
####################################################################


####################################################################
# 確認是否為 Trello Bot 搜尋結果 或 分隔線
####################################################################
def check_comment_div_or_search_result(content=""):
    search_result_title_list = ["精準搜尋", "相關推薦", "你可能也喜歡"]
    # 檢查是否為分隔符號
    if content == "---" or content == "===":
        return True
    # 檢查是否為搜尋結果
    for title in search_result_title_list:
        if f"\n**{title}：**\n" in content:
            return True
    # 都不是回傳非分隔符號與非搜尋結果
    return False
####################################################################
    

####################################################################
# Comment 任務 (搜尋、留言、封面更新)
####################################################################
def process_comment(card_id=""):
    # 檢查卡片 ID 是否存在
    if card_id == "":
        print("卡片 ID 不存在")
        return 404
    # 取得卡片標題
    card_title = trello_connector.getCardTitle(card_id)
    # 如果卡片標題有 [已完成] 則移除
    card_title = card_title.replace("[已完成] ", "")
    # 取得卡片關鍵字
    card_target = answer_core.get_keyword(card_title)
    # 取得卡片留言
    comments_list = trello_connector.getCommentsFromCard(card_id, filter=False)
    # 反轉留言清單(old to new)
    comments_list = comments_list[::-1]
    # 渲染標題（進行中）
    trello_connector.updateDataToCard(card_id, {
        "name" : f"[生成回應中] {card_title}",
    })
    # 設定留言清單成 prompt_list
    prompt_list = [
        {
            "role": "system",
            "content": f"你是一位使用繁體中文的自然科學中學老師正在跟學生交談，主要工作內容會協助中學生研究{card_target}，如果學生有問題則需要根據問題簡單的回答，如果學生沒有問題則基於{card_target}提出相關問題給學生讓學生回答。回答的格式請採用 Markdown 語法。"
        }
    ]
    for comment_obj in comments_list:
        # 取得留言者 ID
        create_id = comment_obj.get("create_id", None)
        # 取得留言內容
        comment_str = comment_obj.get("comment_str", "")
        # 去除機器人TAG
        comment_str = comment_str.replace(f"{TRELLO_BOT_TAG} ", "")
        # 檢查是否為分隔符號或搜尋結果
        if check_comment_div_or_search_result(content=comment_str) is False:
            # Set role of prompt
            if create_id == TRELLO_BOT_ID:
                data_role = "system"
                # 去除機器人回應結尾
                comment_str = comment_str.replace( FOOTER_OF_BOT_REQ , "")
            else:
                data_role = "user"
            # Set prompt
            prompt_list.append({
                "role": data_role,
                "content": comment_str
            })
    print(prompt_list)
    request_str = answer_core.get_gpt_response(
        prompt = prompt_list,
        temperature = 0.5,
        model = "gpt-4-0125-preview"
    )
    trello_connector.addCommentToCard(
        card_id = card_id,
        msgString = request_str + FOOTER_OF_BOT_REQ
    )
    # 更新留言紀錄
    comments_list.append({
        "create_id": TRELLO_BOT_ID,
        "comment_str": request_str
    })
    mongo_connector.update_comment_record(
        card_id = card_id,
        comments_list = comments_list
    )
    # 渲染標題（結束）
    trello_connector.updateDataToCard(card_id, {
        "name" : f"[已完成] {card_title}",
    })
    
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
    #===========================
    print(f" [x] Sent data: {card_id}")
    # 執行 Trello 任務(包含搜尋、留言、封面更新)
    if card_id != "":
        # 執行任務
        process_comment(card_id)
    else:
        # 如果資料為空，則回傳錯誤
        print("\033[0;31m Get Null Data. Please Check Again. \033[0m\n")
####################################################################
    
    
####################################################################
# 连接到RabbitMQ服务器
####################################################################
credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
parameters = pika.ConnectionParameters(RABBITMQ_HOST, RABBITMQ_PORT, '/', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
# 声明一个队列
channel.queue_declare(queue = RABBITMQ_COMMENT_QUEUE)
# 设置消息回调函数
channel.basic_consume(queue = RABBITMQ_COMMENT_QUEUE, on_message_callback=callback, auto_ack=True)
print(f' [*] Q:{RABBITMQ_COMMENT_QUEUE}| Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
####################################################################