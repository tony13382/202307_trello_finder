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


#####################################################################
# 發送文字給 GPT 並取得回應
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
