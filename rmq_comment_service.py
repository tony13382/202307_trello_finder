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
# Import search engine to search article
import modules.search_engine.search_engine as search_engine
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
    article_obj = mongo_connector.find_article_info(article_id)
    url = article_obj["url"]
    showText = article_obj["title"]
    return f" [ \[{showText}\] ]({url}) "
# ------------------------------------------------------------------
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
    pattern = r"\[(\d+)\]"
    replaced_text = re.sub(pattern, lambda match: replace_to_link(match.group(1)), replaced_text)
    # 返回替换后的文本
    return replaced_text
# ------------------------------------------------------------------
def gen_prompt_by_alist(alist=None, max_token_size=MAX_ARTICLE_TOKEN):
    # 定義以使用過的文章 ID
    used_article_id = []
    # 定義 Token Size
    sum_tokens = 0
    if alist is None or len(alist) == 0:
        return {
            "used_alist": used_article_id,
            "prompt": "沒有相關資料可供參考，除非是100%確定的基礎問題否則不回答！"
        }
    else:
        # 組合參考資料
        #data_json_string = """以下是我們給付的參考資料：以 JSON 格式呈現，格式如下{article_id: 文章編號,content : 文章的實際內容,url:網站連結}\n"""
        data_json_string = """以下是我們給付的參考資料：以 JSON 格式呈現，格式如下{article_id: 文章編號,content : 文章的實際內容}\n"""
        # 用迴圈組合參考資料
        for a_id in alist:
            # 根據文章 ID 取得文章資訊
            article_info = mongo_connector.find_article_info(a_id)
            # 組合文章資訊
            contnent_obj = {
                "article_id": article_info.get("link_id", ""),
                "content": article_info.get("content", "")
                #"url": article_info.get("url", "")
            }
            # Get Token Size
            token_size = process_words.get_token_size(
                json.dumps(contnent_obj))["value"]
            # 判斷是否超過最大 Token Size
            if sum_tokens + token_size < max_token_size:
                # 累加 Token Size
                sum_tokens += token_size
                # 累加參考資料
                data_json_string = data_json_string + \
                    json.dumps(contnent_obj, ensure_ascii=False) + "\n"
                # 紀錄使用過的文章 ID
                used_article_id.append(a_id)
            else:
                break
        # 輸出
        print(f"Used Ids: {used_article_id}")
        # 返回結果
        return {
            "used_alist": used_article_id,
            "prompt": data_json_string
        }
# ------------------------------------------------------------------
def gen_prompt_by_comments(comments_list=None):
    new_prompts = []
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
            new_prompts.append({
                "role": data_role,
                "content": comment_str
            })
    return new_prompts
# ------------------------------------------------------------------
def search_and_update_alist(search_method, user_input, used_alist):
    """
    對指定的搜索方法進行搜索，並根據搜索結果更新文章列表和提示信息。

    :param search_method: 搜索引擎的搜索方法
    :param user_input: 用戶輸入的搜尋關鍵字
    :param used_alist: 已經使用過的文章ID列表
    :return: 更新後的添加文章標誌、提示信息和文章ID列表
    """
    # 使用指定的搜索方法進行搜索
    search_result = search_method(user_input=user_input)
    if search_result["state"] is True:
        # 從搜索結果中提取文章ID，支持不同鍵名的ID字段
        article_ids = [article_object.get("article_id") or article_object.get("_id")
                       for article_object in search_result.get("alist", [])]
        # 更新已使用的文章ID列表
        used_alist += article_ids
        # 生成提示信息
        convert_object = gen_prompt_by_alist(used_alist)
        prompt = convert_object.get("prompt", "")
        # 返回是否可添加文章的標誌、提示信息和更新後的文章ID列表
        return convert_object.get("can_add", False), prompt, used_alist
    # 如果搜索結果的狀態不是True，返回None
    return None, None, used_alist
# ------------------------------------------------------------------
def gen_data_prompt_by_str(card_target, target_of_last_comment):
    used_alist = []
    prompt = ""
    can_add_article = True
    # 組合用戶輸入的關鍵字
    user_input = card_target + " " + target_of_last_comment
    # 初始化添加文章的標誌
    can_add_article = True
    # 進行第一次搜索並根據結果更新文章列表和提示信息 TF
    if can_add_article:
        can_add_article, prompt, used_alist = search_and_update_alist(
            search_engine.tf, user_input, used_alist)
    # 如果還可以添加文章，進行第二次搜索 MIX
    if can_add_article:
        can_add_article, prompt, used_alist = search_and_update_alist(
            search_engine.sbert_mix_tf, user_input, used_alist)
    # 如果仍然可以添加文章，進行第三次搜索 SBERT
    if can_add_article:
        can_add_article, prompt, used_alist = search_and_update_alist(
            search_engine.sbert, user_input, used_alist)
    # 返回結果
    return {
        "used_alist": used_alist,
        "prompt": prompt
    }
####################################################################



####################################################################
###                         生成回應邏輯                           ###
####################################################################
def gpt_req_with_article(card_id,card_target,comments_list):
    print("處理 prompt 文章資料")
    # Get Article Info
    topic_articles = mongo_connector.get_trello_log_articles(card_id)
    # 組合參考資料
    sum_tokens = 0
    used_article_id = []
    if(len(topic_articles) > 0):
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
    else:
        data_json_string = "無相關參考資料，除非是基本定義否則不予回答。"
    # -----------------------------------
    # 組合 prompt 清單
    basic_list = [
        {
            "role": "system",
            "content": f"""
                #zh_tw 
                你是一位使用繁體中文的自然科學中學老師，正在跟剛接觸研究領域的學生交談，
                首先學生正在研究{card_target}，而你需要幫助學生瞭解相關知識，
                因此你需要
                1. 基於參考資料嘗試回答學生的問題，並在回答之中強制標注[文章編號]，
                2. 如果參考資料無法解答問題則只告知現有資料無法回答問題。
                3. 最後無論有沒有回答，你都需要追問學生讓學生回答以促進學生對{card_target}深度思考。
                輸出的文本需要基於 Markdown 語法。
            """
        },
        {
            "role": "system",
            "content": data_json_string
        }
    ]
    gpt_prompt = []
    gpt_prompt += basic_list
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
            gpt_prompt.append({
                "role": data_role,
                "content": comment_str
            })
    #prompt_list.append(basic_list)
    # -----------------------------------
    # 準備 GPT Request
    print("發送 GPT Request")
    request_str = answer_core.get_gpt_response(
        prompt=gpt_prompt,
        temperature=0.2,
        model="gpt-4-0125-preview"
    )
    # 替换文本
    replaced_text = replace_article_number(request_str)
    #------------------------------------------------
    for prompt in gpt_prompt:
        print(prompt)
    print("-----------------------------------")
    print(replaced_text)
    print("-----------------------------------")
    print(f"使用文章 ID：{used_article_id}")
    print("-----------------------------------")
    print(f"End of Card ID: {card_id}")
    return {
        "prompt_list": gpt_prompt,
        "request_str": replaced_text
    }
# ------------------------------------------------------------------
def gpt_answer(card_target, comments_list):
    # 取得問題文本
    target_of_last_comment = answer_core.get_keyword(
        comments_list[-1].get("comment_str", ""))
    # 生成相關提示信息
    prompt_obj = gen_data_prompt_by_str(
        card_target, target_of_last_comment)
    data_prompt_str = prompt_obj.get("prompt", "")
    used_alist = prompt_obj.get("used_alist", [])
    # 定義基礎回答方法
    basic_list = [
        {
            "role": "system",
            "content": f"#zh_tw 你是一位使用繁體中文的自然科學中學老師正在跟剛接觸研究領域的學生交談，首先學生正在研究{card_target}，因此你需要基於參考資料的內容回答學生的問題，並標注 [文章編號] ，如果參考資料無法解答問題則只能告知無法回應。輸出的文本需要基於 Markdown 語法。"
        },
        {
            "role": "system",
            "content": data_prompt_str
        }
    ]
    # 組合 prompt 清單
    push_prompt_list = []
    push_prompt_list += basic_list
    push_prompt_list += gen_prompt_by_comments(comments_list)
    # 進行 GPT 回答
    request_str = answer_core.get_gpt_response(
        prompt=push_prompt_list,
        temperature=0.7,
        model= "gpt-4-turbo-preview"
    )
    # 替换文本
    replaced_text = replace_article_number(request_str)
    return {
        "prompt_list": push_prompt_list,
        "request_str": replaced_text,
        "used_alist": used_alist
    }
# ------------------------------------------------------------------
def gpt_ask(card_target, comments_list):
    # 定義基礎回答方法
    basic_list = [
        {
            "role": "system",
            "content": f"#zh_tw 你是一位使用繁體中文的自然科學中學老師正在跟剛接觸研究領域的學生交談，首先學生正在研究{card_target}，而你需要幫助學生瞭解相關知識，因此你需要基於以下聊天內容提出問題給學生讓學生回答以促進學生對{card_target}深度思考。輸出的文本只需要問題絕對不要生成標題，我會自己加上去，輸出使用 Markdown 語法。"
        }
    ]
    # 組合 prompt 清單
    push_prompt_list = []
    push_prompt_list += basic_list
    push_prompt_list += gen_prompt_by_comments(comments_list)
    # 進行 GPT 回答
    request_str = answer_core.get_gpt_response(
        prompt=push_prompt_list,
        temperature=0.7,
        model="gpt-4-turbo-preview"
    )
    return {
        "prompt_list": push_prompt_list,
        "request_str": request_str
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
    card_title = trello_connector.getCardTitle(card_id,filter=True)
    # 取得卡片關鍵字
    card_target = answer_core.get_keyword(card_title)
    # 取得卡片留言(New to Old)
    comments_list = get_comment_comments(card_id)
    # 渲染標題（進行中）
    trello_connector.updateDataToCard(card_id, {
        "name" : f"[生成回應中] {card_title}",
    })
    # 生成回應
    print("正在回答...")
    # 生成回應
    answer_req_obj = gpt_answer(card_target, comments_list)
    answer_req = answer_req_obj.get("request_str", "")
    # 留言回應
    trello_connector.addCommentToCard(
        card_id = card_id,
        msgString = answer_req + FOOTER_OF_BOT_REQ
    )
    print("正在出題...")
    # 新增資料到 comment_list
    new_comments_list = comments_list + \
        [{"create_id": "5cf78be21c83121944069409", "comment_str": answer_req}]
    # 生成問題
    question_req = gpt_ask(card_target, new_comments_list).get("request_str", "")
    # 留言回應
    trello_connector.addCommentToCard(
        card_id = card_id,
        msgString = "###除此之外，你可以想一想\n\n" + question_req + FOOTER_OF_BOT_REQ
    )
    print("生成完成！")
    
    combine_rq = f"{answer_req}\n\n---\n\n{question_req}"    
    """
    # 留言回應
    trello_connector.addCommentToCard(
        card_id = card_id,
        msgString = combine_rq + FOOTER_OF_BOT_REQ
    )
    """
    new_comments_list = comments_list + \
        [{"create_id": "5cf78be21c83121944069409", "comment_str": question_req}]
    
    mongo_connector.add_comment_log(
        card_id = card_id,
        state = True,
        msg = "成功新增回應與問題！",
        comments_list = new_comments_list,
        more_info= {
            "article_list" : answer_req_obj.get("used_alist", [])
        }
    )
    
    # 更新留言紀錄
    comments_list.append({
        "create_id": TRELLO_BOT_ID,
        "comment_str": combine_rq
    })
    mongo_connector.update_comment_record(
        card_id = card_id,
        comments_list = new_comments_list
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
        mongo_connector.add_comment_log(
            card_id = card_id,
            state = False,
            msg = "Get Null Data. Please Check Again！",
            comments_list = []
        )
####################################################################
    
    
####################################################################
# 连接到RabbitMQ服务器
####################################################################
credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
#parameters = pika.ConnectionParameters(RABBITMQ_HOST, RABBITMQ_PORT, '/', credentials)
parameters = pika.ConnectionParameters(
    host= RABBITMQ_HOST,
    port=RABBITMQ_PORT,
    virtual_host='/',
    credentials=credentials,
    heartbeat = 180  # 設定心跳間隔為 180 秒 / 3mins
)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
# 声明一个队列
channel.queue_declare(queue = RABBITMQ_COMMENT_QUEUE)
# 设置消息回调函数
channel.basic_consume(queue = RABBITMQ_COMMENT_QUEUE, on_message_callback=callback, auto_ack=True)
print(f' [*] Q:{RABBITMQ_COMMENT_QUEUE}| Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
####################################################################