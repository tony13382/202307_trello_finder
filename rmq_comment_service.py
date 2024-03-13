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
# Token Size Get
import modules.tools.process_words as process_words
# 用於 rabbitMQ （接收訊息）
import pika
import json
import re


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
# ---------------------------------------------------------------
# Token Size Setup
MAX_ARTICLE_TOKEN = config['ai_core']['open_ai_max_article_tokens']
MAX_COMMENT_TOKEN = config['ai_core']['open_ai_max_comment_tokens']
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
# 整理留言清單
####################################################################
def get_comment_comments(card_id, max_token_size=MAX_COMMENT_TOKEN):
    # 取得卡片留言(New to Old)
    comments_list = trello_connector.getCommentsFromCard(card_id, filter=False)
    # 計算 Token Size
    total_token_size = 0
    new_comments_list = []
    for comment_obj in comments_list:
        if total_token_size < max_token_size:
            # 取得文本
            comment_str = comment_obj.get("comment_str", "")
            # 取得Token Size
            try:
                token_size = process_words.get_token_size(comment_str)["value"]
            except Exception as e:
                print(f"取得 Token Size 時發生錯誤：{e}")
                break
            # 判斷是否累加
            if total_token_size + token_size < max_token_size:
                total_token_size += token_size
                new_comments_list.append(comment_obj)
            else:
                # 超過最大Token Size，退出迴圈
                break
    # 反轉留言清單(old to new)
    new_comments_list = new_comments_list[::-1]
    return new_comments_list
####################################################################


####################################################################
# 整理文本 For (gpt_req_with_article)
####################################################################
def replace_to_link(article_id):
    url = mongo_connector.find_article_info(article_id)["url"]
    return f" [文章編號: {article_id}]({url})"
def replace_article_number(text):
    # 使用正则表达式查找格式为 [文章編號: 数字] 的文本
    # 用 get_info 函数的结果替换找到的文本
    # re.sub 的第二个参数使用了一个 lambda 函数，以便传递匹配到的数字给 get_info 函数
    pattern = r"\[文章編號: (\d+)\]"
    replaced_text = re.sub(pattern, lambda match: replace_to_link(match.group(1)), text)
    pattern = r"\[文章編號：(\d+)\]"
    replaced_text = re.sub(pattern, lambda match: replace_to_link(match.group(1)), replaced_text)
    pattern = r"\[文章編號:(\d+)\]"
    replaced_text = re.sub(pattern, lambda match: replace_to_link(match.group(1)), replaced_text)
    # 返回替换后的文本
    return replaced_text
####################################################################


####################################################################
###                         生成回應邏輯                           ###
####################################################################
def gpt_req_pure(card_target,comments_list):
    # 設定留言清單成 prompt_list
    prompt_list = [
        {
            "role": "system",
            "content": f"#zh_tw 你是一位使用繁體中文的自然科學中學老師正在跟學生交談，主要工作內容會協助中學生研究{card_target}，如果學生有問題則需要根據問題簡單的回答，如果學生沒有問題則基於{card_target}提出相關問題給學生讓學生回答。回答的格式請採用 Markdown 語法。"
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
                comment_str = comment_str.replace(FOOTER_OF_BOT_REQ, "")
            else:
                data_role = "user"
            # Set prompt
            prompt_list.append({
                "role": data_role,
                "content": comment_str
            })
    # -----------------------------------
    # 準備 GPT Request
    request_str = answer_core.get_gpt_response(
        prompt=prompt_list,
        temperature=0.5,
        model="gpt-4-0125-preview"
    )
    # -----------------------------------
    for prompt in prompt_list:
        print(prompt)
    print("-----------------------------------")
    print(request_str)
    return {
        "prompt_list": prompt_list,
        "request_str": request_str
    }
# ------------------------------------------------------------------
def gpt_req_with_article(card_id,card_target,comments_list):
    print("處理 prompt 文章資料")
    # Get Article Info
    topic_articles = mongo_connector.get_trello_log_articles(card_id)
    # 組合參考資料
    sum_tokens = 0
    used_article_id = []
    data_json_string = """以下是我們給付的參考資料：以 JSON 格式呈現，格式如下{article_id: 文章編號,content : 文章的實際內容,url:網站連結}\n"""
    for a_id in topic_articles:
        article_info = mongo_connector.find_article_info(a_id)
        contnent_obj = {
            "article_id": article_info.get("link_id", ""),
            "content" : article_info.get("content", ""),
            "url": article_info.get("url", "")
        }
        # Get Token Size
        token_size = process_words.get_token_size(json.dumps(contnent_obj))["value"]
        if sum_tokens + token_size < MAX_ARTICLE_TOKEN:
            sum_tokens += token_size
            data_json_string += json.dumps(contnent_obj, ensure_ascii=False)
            used_article_id.append(a_id)
        else:
            break
    # -----------------------------------
    # 組合 prompt 清單
    basic_list = [
        {
            "role": "system",
            "content": f"#zh_tw 你是一位使用繁體中文的自然科學中學老師正在跟學生交談，主要工作內容會協助中學生研究{card_target}，如果學生有問題則需要根據結合參考資料與問題進行回答並標注[文章編號]，如果參考資料無法解答問題則只能告知無法回應。學生沒有問題則基於{card_target}提出相關問題給學生讓學生回答。請採用 Markdown 語法回答。"
        },
        {
            "role": "system",
            "content": data_json_string
        }
    ]
    prompt_list2 = []
    prompt_list2 += basic_list
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
                comment_str = comment_str.replace(FOOTER_OF_BOT_REQ, "")
            else:
                data_role = "user"
            # Set prompt
            prompt_list2.append({
                "role": data_role,
                "content": comment_str
            })
    #prompt_list.append(basic_list)
    # -----------------------------------
    # 準備 GPT Request
    print("發送 GPT Request")
    request_str = answer_core.get_gpt_response(
        prompt=prompt_list2,
        temperature=0.5,
        model="gpt-4-0125-preview"
    )
    # 替换文本
    replaced_text = replace_article_number(request_str)
    #------------------------------------------------
    for prompt in prompt_list2:
        print(prompt)
    print("-----------------------------------")
    print(replaced_text)
    print("-----------------------------------")
    print(f"使用文章 ID：{used_article_id}")
    return {
        "prompt_list": prompt_list2,
        "request_str": replaced_text
    }
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
    # 取得卡片留言(New to Old)
    comments_list = get_comment_comments(card_id)
    # 渲染標題（進行中）
    trello_connector.updateDataToCard(card_id, {
        "name" : f"[生成回應中] {card_title}",
    })
    """
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
    """
    # 生成回應
    request_str = gpt_req_with_article(card_id,card_target,comments_list).get("request_str", "")
    # 留言回應
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