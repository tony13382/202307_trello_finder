# coding:utf-8
import ast

from flask import Flask
from flask import render_template, jsonify
from flask import request
import json

# Setup environment value
import os
from dotenv import load_dotenv
load_dotenv()

# SBERT 編碼模組
from toolbox.embed import embedding_sentence
# Milvus 向量搜尋與運算模組
from toolbox.vector_search import search_vector
# MongoDB 文章搜尋模組
from toolbox.mongo_connector import article_search,add_trello_log
# GPT 回答模組
from toolbox.answer_core import qa_by_anthropic, qa_by_openai, qa_by_RoBERTa, qa_by_bert
# Trello 模組
from toolbox.trello_connector import updateDataToCard, addCommentToCard, addCommentWithPictureToCard

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
# roBERTa_setup : Boolean (預設為 False, True 時會使用 GPT 回答問題)
# bert_setup : Boolean (預設為 False, True 時會使用 GPT 回答問題)
#-------------------
# Response Value
# state : Boolean
# result : [
#     {} * limit //Top-K Items
# ]
####################

# 預處理 Milvus 回傳的資料
def process_milvus_result(req_array, sentence ,anthropic_setup=False,openai_setup=False,roBERTa_setup=False,bert_setup=False):
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
                answer = qa_by_anthropic(article['value']['content'], sentence)
                if(answer['state']):
                    insert_data["answer_by_anthropic"] = answer['value']
                else:
                    return {
                        "state" : False,
                        "err_msg" : answer['value'],
                        "show_msg" : "anthropic GPT 模組失敗，請聯絡工程人員",
                        "error_code" : 504,
                    }
            # Use Meta's content to answer question by openai
            if openai_setup:
                answer = qa_by_openai(article['value']['content'], sentence)
                if(answer['state']):
                    insert_data["answer_by_openai"] = answer['value']
                else:
                    return {
                        "state" : False,
                        "err_msg" : answer['value'],
                        "show_msg" : "openai GPT 模組失敗，請聯絡工程人員",
                        "error_code" : 504,
                    }
            # Use Meta's content to answer question by RoBERTa
            if roBERTa_setup:
                answer = qa_by_RoBERTa(article['value']['content'], sentence)
                if(answer['state']):
                    insert_data["answer_by_RoBERTa"] = answer['value']
                else:
                    return {
                        "state" : False,
                        "err_msg" : answer['value'],
                        "show_msg" : "RoBERTa GPT 模組失敗，請聯絡工程人員",
                        "error_code" : 504,
                    }
            # Use Meta's content to answer question by RoBERTa
            if bert_setup:
                answer = qa_by_bert(article['value']['content'], sentence)
                if(answer['state']):
                    insert_data["answer_by_BERT"] = answer['value']
                else:
                    return {
                        "state" : False,
                        "err_msg" : answer['value'],
                        "show_msg" : "BERT GPT 模組失敗，請聯絡工程人員",
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
    
    # Get Value Setup
    if "limit" in setup:
        limit = setup["limit"]
    else:
        limit = 10
    
    if "anthropic_setup" in setup:
        anthropic_setup = setup["anthropic_setup"]
    else:
        anthropic_setup = False
    
    if "openai_setup" in setup:
        openai_setup = setup["openai_setup"]
    else:
        openai_setup = False

    if "roBERTa_setup" in setup:
        roBERTa_setup = setup["roBERTa_setup"]
    else:
        roBERTa_setup = False

    if "bert_setup" in setup:
        bert_setup = setup["bert_setup"]
    else:
        bert_setup = False
    
    
    # Search By Vector
    if(q_vector["state"]):
        limit = int(limit)
    
        # Get Similar Article
        result = search_vector(q_vector["value"], limit=limit)
        
        if(result['state']):
            try:
                # 處理資料
                return_array = process_milvus_result(
                    result['value'], 
                    sentence, 
                    anthropic_setup = anthropic_setup,
                    openai_setup = openai_setup,
                    roBERTa_setup = roBERTa_setup,
                    bert_setup = bert_setup,
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
        # Get Limit
        get_limit = request.args.get('limit',10)
        # Get Anthropic Setup
        anthropic_setup = request.args.get('anthropic_setup',False)
        # Get OpenAI Setup
        openai_setup = request.args.get('openai_setup',False)
        # Get RoBERTa Setup
        roBERTa_setup = request.args.get('roBERTa_setup',False)
        # Get BERT Setup
        bert_setup = request.args.get('bert_setup',False)

        # Get Search Result
        result = process_sentence_to_article_list(sentence,setup={
            "limit" : get_limit,
            "anthropic_setup" : anthropic_setup,
            "openai_setup" : openai_setup,
            "roBERTa_setup" : roBERTa_setup,
            "bert_setup" : bert_setup,
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
trello_request_limit = int(os.getenv("trello_request_limit"))
def process_webhook(data):
    try:
        # Convert Data
        print(data)
        user_input = data["user_input"]
        card_id = data["card_id"]

        # Get Search Result
        anthropic_setup = bool(os.getenv("anthropic_setup"))
        openai_setup = bool(os.getenv("openai_setup"))
        roBERTa_setup = bool(os.getenv("roBERTa_setup"))
        bert_setup = bool(os.getenv("bert_setup"))

        result_of_sentence = process_sentence_to_article_list(user_input,setup={
            "limit" : trello_request_limit,
            "anthropic_setup" : anthropic_setup,
            "openai_setup" : openai_setup,
            "roBERTa_setup" : roBERTa_setup,
            "bert_setup" : bert_setup,
        })
        
        if(result_of_sentence['state']):
            # Add Comment
            for item in result_of_sentence['result']:
                commit_msg = f"參考資料：\n[{item['title']}]({item['url']}) \n"
                if(anthropic_setup):
                    commit_msg += f"參考回答 A ：\n{item['answer_by_anthropic']} \n"
                if(openai_setup):
                    commit_msg += f"參考回答 C ：\n{item['answer_by_openai']} \n"
                # Add Comment
                try:
                    addCommentToCard(card_id,commit_msg)
                except Exception as exp:
                    return {
                        "state" : False,
                        "err_msg" : str(exp),
                        "show_msg" : "[addCommentToCard] 留言失敗",
                    }
            
            # List of All comment Done
            try:
                updateDataToCard(card_id, {
                    "name" : f"[已完成] {user_input}",
                })
                return {
                    "state" : True,
                    "show_msg" : "留言成功",
                }
            except Exception as exp:
                return {
                    "state" : False,
                    "err_msg" : str(exp),
                    "show_msg" : "[updateDataToCard] 卡片更新失敗",
                }
        else:
            return {
                "state" : False,
                "err_msg" : result_of_sentence['err_msg'],
                "show_msg" : "[result_of_sentence] " + result_of_sentence['show_msg'],
            }
    except Exception as exp:
        return {
            "state" : False,
            "err_msg" : str(exp),
            "show_msg" : "[process_webhook] 資料處理失敗，請聯絡工程人員",
        }

@app.route('/webhook',methods=['POST','HEAD','GET'])
def webhook_post():
    if request.method == 'POST':
        try:
            req = request.json
            try:
                if(req["action"]["type"] == "createCard"):
                    # Get Data
                    print("偵測到新增卡片")
                    user_input = req["action"]["data"]["card"]["name"]
                    card_id = req["action"]["data"]["card"]["id"]
                    ##board_id = req["action"]["data"]["board"]["id"]
                    
                    # Start to Search and Add Comment
                    process_satae = process_webhook({
                        "user_input" : user_input,
                        "card_id" : card_id,
                    })

                    # Add Log to Server
                    if(process_satae['state']):
                        add_trello_log(card_id, True, process_satae["show_msg"])
                    else:
                        add_trello_log(card_id, False,process_satae["show_msg"] + "\n\n" + process_satae["err_msg"])
                
                #add_trello_log(card_id, True, "Card Create")
            except:
                pass
        except:
            print("null Request")

    return ("", 200)

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0")