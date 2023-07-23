from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
anthropic = Anthropic(api_key="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")

import openai
openai.api_key = "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"

def generate_prompt(source_content,question):
    return f"""Human: 
            我會給你一份檔案。 然後我會向你提問， 利用檔案內的內容來回答。 這是檔案內容：      
            {source_content}
            \n
            採用我提供的資料用繁體中文嘗試回答：{question}，如果發現內容無法回答則回覆「無法提供最佳答案」。
            這是單次問答無須說明開頭與結尾 \nAssistant:
        """

def qa_by_anthropic(source_content, question):
    try:
        completion = anthropic.completions.create(
            model="claude-1",
            max_tokens_to_sample=300,
            prompt= generate_prompt(source_content,question),
        )
        return {
            "state": True,
            "value": completion.completion,
        }
    except Exception as exp:
        return {
            "state": False,
            "value": str(exp),
       }
    

def qa_by_openai(source_content,question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"我會給你一份檔案。 然後我會向你提問， 利用檔案內的內容來回答。如果發現內容無法回答則回覆「無法提供最佳答案」。這是檔案內容：{source_content}" },
                {"role": "user", "content": f"採用我提供的資料用繁體中文嘗試回答：{question}，這是單次問答無須說明開頭與結尾。" }
            ],
            temperature=0,
        )
        return {
            "state": True,
            "value": response['choices'][0]['message']['content'],
        }
    except  Exception as exp:
        return {
            "state": False,
            "value": str(exp),
       }