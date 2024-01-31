# coding:utf-8
import openai
import os

openai_api_key = os.getenv("openai_api_key")
openai_gpt_model = "gpt-3.5-turbo"

openai.api_key = openai_api_key

def qa_by_gpt3(question):

    response = openai.ChatCompletion.create(
        model=openai_gpt_model,
        messages=[
            {"role": "system", "content": "你是中學生的問答助理，請幫我以中學生易懂的方式回答問題。"},
            {"role": "user", "content": "請用中文回答或解釋以下問題：" + str(question).encode("utf-8").decode("latin1") }
        ],
        temperature=0,
        max_tokens=500,
    )
    print("Response:", response)
    return {
        "state": True,
        "value": response['choices'][0]['message']['content'],
    }


print(qa_by_gpt3("三角函數是什麼"))

