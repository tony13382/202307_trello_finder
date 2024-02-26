# coding:utf-8
####################################################################
# 載入環境變數
####################################################################
import yaml
with open('config.yml', 'r', encoding='utf-8') as config_File:
    config = yaml.safe_load(config_File)
OPENAI_MAX_TOKENS = config["ai_core"]["open_ai_max_tokens"]
####################################################################


####################################################################
# 取得 Token 數量
# 參考資料：
# https://github.com/DjangoPeng/openai-quickstart/blob/main/openai_api/count_tokens_with_tiktoken.ipynb
####################################################################
import tiktoken
encoding = tiktoken.get_encoding("cl100k_base")
# 取得 Token 數量
def get_token_count(text):
    return len(encoding.encode(text))
def check_token_in_limit(text):
    return get_token_count(text) <= OPENAI_MAX_TOKENS
####################################################################


####################################################################
# OpenAI API Key & Settings
####################################################################
from openai import OpenAI
OPENAI_API_KEY = config["ai_core"]["open_ai"]
OPENAI_GPT_MODEL = "gpt-3.5-turbo-16k"
client = OpenAI(
    api_key = OPENAI_API_KEY,
)
####################################################################


####################################################################
# 執行文章查詢
from modules.tools.mongo_connector import find_article_info
####################################################################


#####################################################################
# 發送文字給 GPT-3.5 並取得回應
####################################################################
def get_gpt_response(prompt = None, file_gpt_ids = None, temperature = 0.1, model = OPENAI_GPT_MODEL, max_tokens = None):
    if file_gpt_ids is None:
        file_gpt_ids = []
    # 檢查 Token 數量是否超過限制
    combine_str = ""
    for con in prompt:
        combine_str += con['content']
    if check_token_in_limit(combine_str) == False:
        return "Token 數量超過限制"
    if prompt is None:
        return "請輸入提示文字"
    # 跟 GPT-3.5 互動
    completion = client.chat.completions.create(
        model = model,
        temperature = temperature,
        messages = prompt,
        max_tokens = max_tokens
    )
    return completion.choices[0].message.content
####################################################################


####################################################################
# 利用文章列表與問題回答問題
def answer_question(article_list,question):
    # 設定回答內容
    GPT_SYSTEM_MSG = "你是一位老師，學生會問你問題，你只能依據參考資料用繁體中文回答問題或說明文件與問題的相關性。參考資料格式如下：[1]'參考資料內容'。" #Token = 88
    gpt_user_msg_q = f"學生問題：{question}" #Token = 7+
    gpt_user_msg_a = f"，參考資料：" #Token = 8+
    gpt_user_article = "" 
    footer_msg = "\n---\n參考資料：\n"
    # 設定參考資料
    q_tokens = get_token_count(GPT_SYSTEM_MSG + gpt_user_msg_q)
    a_tokens = 0
    for index in article_list:
        # 取得文章資訊
        article_data = find_article_info(str(index))
        # 計算 Token 數量
        a_tokens += get_token_count(article_data['content'])
        # 判斷 Token 數量是否超過限制
        if q_tokens + a_tokens < OPENAI_MAX_TOKENS:
            # 組合參考資料到 user prompt
            gpt_user_article += f"[{index}]{article_data['content']}\n"
            # 組合 footer 資料
            footer_msg += f"- [{index}] [{article_data['title']}]({article_data['url']})\n"
        else:
            # 超過限制就跳出迴圈
            break

    # 組合 prompt
    gpt_user_msg_a += gpt_user_article
    # 跟 GPT-3.5 互動
    req_str = get_gpt_response(
        prompt= [
            {"role": "system", "content": GPT_SYSTEM_MSG}, 
            {"role": "user", "content": gpt_user_msg_q + gpt_user_msg_a}
        ])
    # 回傳 GPT-3.5 的回答 與 footer 資料（參考資訊訊息）
    return req_str + footer_msg
####################################################################


####################################################################
# 利用 GPT 助理萃取關鍵字
####################################################################
def get_keyword(text):
    prompt = f"你是一位老師，要幫我把學生的提問挑出關鍵字直接回應，不用開頭與備註，例如：「小幫手我想知道亨利定律公式」輸出「亨利定律」；「小幫手我想問虎克定律」輸出「虎克定律」；「小幫手我想知道同種橡皮筋的並聯條數是否影響彈性係數」輸出「並聯、彈性係數」，接下來我會給你文字請根據前面需求轉換文字，沒給文字不回應，請幫我把「{text}」的關鍵字截出來"
    return get_gpt_response(prompt = [
        {"role": "user", "content": prompt},
    ])
####################################################################