# coding:utf-8
import ast

from flask import Flask
from flask import render_template, jsonify
from flask import request
import json

# SBERT 編碼模組
from toolbox.embed import embedding_sentence
# Milvus 向量搜尋與運算模組
from toolbox.vector_search import search_vector
# MongoDB 文章搜尋模組
from toolbox.mongo_search import article_search
# Anthropic GPT 回答模組
from toolbox.gpt import qa_by_anthropic, qa_by_openai


app = Flask(__name__)

@app.route('/',methods=['GET'])
def index():
    return render_template('index.html')


# 轉換文本至向量
####################
# Request Value
# sentence : String
#-------------------
# Response Value
# state : Boolean
# result : [] Array(768)
####################
@app.route('/vector', methods=['POST'])
def vector_get():
    try:
        # Get Request Value
        sentence = request.args.get('sentence')

        # Get Embedding Vector
        result = embedding_sentence(sentence)
        if result["state"]:
            return jsonify({
                "state": True,
                "sentence": sentence,
                "embedding": result["value"]
            })
        else:
            return jsonify({
                "state": False,
                "err_msg": result["value"],
                "show_msg": "模組失敗，請聯絡工程人員",
                "error_code": 501,
            })

    except Exception as exp:
        return jsonify({
            "state": False,
            "err_msg": str(exp),
            "show_msg": "系統失敗，請聯絡工程人員",
            "error_code": 500,
        })


#獲取相近的文本（by vector）
####################
# Request Value
# vector : [] Array(768)
# limit : Int
#-------------------
# Response Value
# state : Boolean
# result : [
#     {} * limit //Top-K Items
# ]
#################### 
@app.route('/vector',methods=['GET'])
def vector_post():
    try:
        # Get Request Value
        q_vector = ast.literal_eval(request.args.get('vector'))
        limit = int(request.args.get('limit'))
        print(q_vector)
        print(limit)
        # Get Similar Article
        result = search_vector(q_vector, limit=limit)
        if(result['state']):
            return jsonify({
                "state" : True,
                "result" : result['value'],
            })
        else:
            return jsonify({
                "state" : False,
                "err_msg" : result['value'],
                "show_msg" : "系統模組失敗，請聯絡工程人員",
                "error_code" : 501,
            })
        
    except Exception as exp:
        return jsonify({
            "state" : False,
            "err_msg" : str(exp),
            "show_msg" : "系統失敗，請聯絡工程人員",
            "error_code" : 500,
        })
    

#獲取相近的文本（by sentence）
####################
# Request Value
# sentence : String
# limit : Int
# anthropic_setup : Boolean (預設為 False, True 時會使用 GPT 回答問題)
# openai_setup : Boolean (預設為 False, True 時會使用 GPT 回答問題) 
#-------------------
# Response Value
# state : Boolean
# result : [
#     {} * limit //Top-K Items
# ]
####################

# 預處理 Milvus 回傳的資料
def process_milvus_result(req_array, sentence ,anthropic_setup=False,openai_setup=False):
    return_array = []
    for item in req_array:
        # Use track_id to find Ariicle (Only one article)
        article_id = item['track_id']
        article = article_search(article_id)
        if(article['state']):
            insert_data = {
                "id" : item['id'],
                "distance" : item['distance'],
                "title" : article['value']['title'],
                "url" : article['value']['url'],
            }
            # Use Meta's content to answer question by gpt
            if anthropic_setup:
                answer = qa_by_anthropic(article['value']['title'], sentence)
                if(answer['state']):
                    insert_data["answer_by_anthropic"] = answer['value']
                else:
                    return {
                        "state" : False,
                        "err_msg" : answer['value'],
                        "show_msg" : "GPT 模組失敗，請聯絡工程人員",
                        "error_code" : 504,
                    }
            # Use Meta's content to answer question by openai
            if openai_setup:
                answer = qa_by_openai(article['value']['title'], sentence)
                if(answer['state']):
                    insert_data["answer_by_openai"] = answer['value']
                else:
                    return {
                        "state" : False,
                        "err_msg" : answer['value'],
                        "show_msg" : "GPT 模組失敗，請聯絡工程人員",
                        "error_code" : 504,
                    }
        else:
            print(article['value'], "cannot find")
        
        return_array.append(insert_data)

    # End of Combine amd return the value
    return {
        "state" : True,
        "result" : return_array,
    }

def process_sentence_to_article_list(sentence,setup):
    # Get Embedding Vector
    q_vector = embedding_sentence(sentence)
    # Get Anthropic Setup
    anthropic_setup = setup["anthropic_setup"]
    # Get OpenAI Setup
    openai_setup = setup["openai_setup"]
    # Search By Vector
    if(q_vector["state"]):
        limit = int(request.args.get('limit'))
    
        # Get Similar Article
        result = search_vector(q_vector["value"], limit=limit)
        
        if(result['state']):
            try:
                # 處理資料
                return_array = process_milvus_result(
                    result['value'], 
                    sentence, 
                    anthropic_setup=anthropic_setup,
                    openai_setup=openai_setup
                )
                if(return_array['state']):
                    return {
                        "state" : True,
                        "result" : return_array['result'],
                    }
                else:
                    return {
                        "state" : False,
                        "err_msg" : return_array['err_msg'],
                        "show_msg" : return_array['show_msg'],
                        "error_code" : return_array['error_code'],
                    }
            
            except Exception as exp:
                return {
                    "state" : False,
                    "err_msg" : str(exp),
                    "show_msg" : "Data Combine 模組失敗，請聯絡工程人員",
                    "error_code" : 503,
                }
        else:
            return {
                "state" : False,
                "err_msg" : result['value'],
                "show_msg" : "系統模組（search_vector）失敗，請聯絡工程人員",
                "error_code" : 501,
            }
    else:
        return {
            "state" : False,
            "err_msg" : q_vector["value"],
            "show_msg" : "模組失敗，請聯絡工程人員",
            "error_code" : 501,
        }

# Flask API
@app.route('/article',methods=['GET'])
def article_get():
    try:
        # Get Request Value
        sentence = request.args.get('sentence')
        # Get Anthropic Setup
        anthropic_setup = request.args.get('anthropic_setup',False)
        # Get OpenAI Setup
        openai_setup = request.args.get('openai_setup',False)
        # Get Search Result
        result = process_sentence_to_article_list(sentence,setup={
            "anthropic_setup" : anthropic_setup,
            "openai_setup" : openai_setup,
        })
        # Return Result
        return jsonify(result)
        
    except Exception as exp:
        return jsonify({
            "state" : False,
            "err_msg" : str(exp),
            "show_msg" : "系統失敗，請聯絡工程人員",
            "error_code" : 500,
        })


# Webhook API
@app.route('/webhook',methods=['POST','HEAD','GET'])
def webhook_post():
    if request.method == 'POST':
        try:
            req = request.json
            try:
                if(req["action"]["type"] == "createCard"):
                    print("Card Create")
                    user_input = req["action"]["data"]["card"]["name"]
                    card_id = req["action"]["data"]["card"]["id"]
                    board_id = req["action"]["data"]["board"]["id"]
                    print("Get String:",user_input)
                    print("Get ID:", card_id)
                    print("Get Board ID:", board_id)
                #print(request.json)
            except:
                pass
        except:
            print("null Request")

    return ("", 200)

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0")