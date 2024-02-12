# coding:utf-8

# 載入環境變數
import yaml
with open('config.yml', 'r', encoding='utf-8') as config_File:
    config = yaml.safe_load(config_File)

# 取得 Token 數量
# 參考資料：
# https://github.com/DjangoPeng/openai-quickstart/blob/main/openai_api/count_tokens_with_tiktoken.ipynb
import tiktoken
encoding = tiktoken.get_encoding("cl100k_base")

# OpenAI API Key & Settings
from openai import OpenAI
OPENAI_API_KEY = config["answer_core"]["open_ai"]
OPENAI_GPT_MODEL = "gpt-3.5-turbo-16k"
client = OpenAI(
    api_key = OPENAI_API_KEY,
)

# 執行文章查詢
from mongo_connector import find_article_info


# 取得 Token 數量
def get_token_count(text):
    return len(encoding.encode(text))


# 回答問題
def answer_question(article_list,question):
    MAX_TOKENS = 15600
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
        if q_tokens + a_tokens < MAX_TOKENS:
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
    completion = client.chat.completions.create(
        model = OPENAI_GPT_MODEL,
        temperature= 0.1,
        messages=[
            {"role": "system", "content": GPT_SYSTEM_MSG}, 
            {"role": "user", "content": gpt_user_msg_q + gpt_user_msg_a},
        ]
    )
    # 回傳 GPT-3.5 的回答 與 footer 資料（參考資訊訊息）
    return completion.choices[0].message.content + footer_msg


#print(answer_question(
    article_list = [4448,3383,2705],
    question = "虎克定律是什麼?"
#))

print(answer_question(
    article_list = [8451,17685,8775,5743,8734,19661],
    question = "量子力學是什麼?"
))
    
#print(answer_question(article_list = [4448,3383,2705],question = "虎克定律是什麼?"))
