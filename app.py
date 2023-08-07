# coding:utf-8
import ast # 用於將字串轉換成串列
import re

from flask import Flask
from flask import render_template, jsonify, redirect
from flask import request

# 用於隨機抽取回應（無答案時）
import random

# +-------------------------------------------------------+
# Setup environment value
import os
from dotenv import load_dotenv
load_dotenv()
distance_filter = float(os.getenv("distance_filter"))
flask_server_port = int(os.getenv("flask_server_port"))


# 讀取文字檔並轉換成串列
def txt_to_list(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.readlines()
            content = [line.strip() for line in content]
        return content
    except FileNotFoundError:
        print("找不到指定的檔案。請檢查檔案路徑是否正確。")
        return []
    except Exception as e:
        print("讀取檔案時發生錯誤：", e)
        return []

# 指定文字檔路徑
file_path = 'your_file.txt'  # 請替換成實際的檔案路徑
action_word_list = txt_to_list("./setting/action_word_list.txt")
not_found_msg_list = txt_to_list("./setting/not_found_msg_list.txt")
print("啟動詞與無資料罐頭訊息載入完成！")
# +-------------------------------------------------------+


# SBERT 編碼模組
from toolbox.process_words import embedding_sentence, process_sentence, generate_wordcloud
# Milvus 向量搜尋與運算模組
from toolbox.vector_search import search_vector
# MongoDB 文章搜尋模組
from toolbox.mongo_connector import article_search,add_trello_log
# GPT 回答模組
from toolbox.answer_core import qa_by_anthropic, qa_by_openai, qa_by_RoBERTa, qa_by_bert
# Trello 模組
from toolbox.trello_connector import updateDataToCard, addCommentToCard, addCommentWithPictureToCard, addCoverToCard
# Vector 計算模組
import toolbox.vector_calc as vector_calculation


app = Flask(__name__,static_url_path='/imgs',static_folder='static/images/')

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
#     {} * 0~limit //Top-K Items
# ]
####################
# 預處理 Milvus 回傳的資料
def process_milvus_result(req_array, sentence ,anthropic_setup=False,openai_setup=False,roBERTa_setup=False,bert_setup=False):
    return_array = []
    for item in req_array:
        # IF distance < 設定值, break and return 相關性不足的文章
        if(item['distance'] < distance_filter):
            break

        # Use track_id to find Ariicle (Only one article)
        article_id = item['track_id']
        article = article_search(article_id)
        if(article['state']):
            insert_data = {
                "id" : item['id'],
                "distance" : item['distance'],
                "title" : article['value']['title'],
                "url" : article['value']['url'],
                "content" : article['value']['content'],
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
    # 處理句子
    orginal_sentence = process_sentence(sentence, close_word_search_setup = False )
    fuzzy_sentence = process_sentence(sentence)
    
    # 轉換成向量
    o_vector = embedding_sentence(orginal_sentence)
    f_vector = embedding_sentence(fuzzy_sentence)
    q_vector = f_vector

    
    ## 權重計算與調整
    orginal_weight = 1
    fuzzy_weight = 1


    if(o_vector['state'] and f_vector['state']):
        q_vector["value"] = vector_calculation.calc_array_mean(
            set = [{
                "array" : o_vector['value'],
                "weight" : orginal_weight,
            },{
                "array" : f_vector['value'],
                "weight" : fuzzy_weight,
            }],
            len_array = 768
        )
    else:
        return {
            "state" : False,
            "err_msg" : "句子轉換向量失敗\n" + o_vector['value'] + "\n\n" + f_vector['value'],
            "show_msg" : "句子轉換向量失敗，請聯絡工程人員",
            "error_code" : 504,
        }
    
    # Get Value Setup
    if "limit" in setup:
        limit = setup["limit"]
    else:
        limit = 10
    
    if "offset" in setup:
        offset = setup["offset"]
    else:
        offset = 0
    
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
        offset = int(offset)
    

        # Get Similar Article
        result = search_vector(q_vector["value"], limit=limit, offset=offset)
        
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
        # Get Limit
        get_offset = request.args.get('offset',10)
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
            "offset" : get_offset,
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
# Get Environment Value
anthropic_setup = os.getenv("anthropic_setup") in ["True", "true", "1"]
openai_setup = os.getenv("openai_setup") in ["True", "true", "1"]
roBERTa_setup = os.getenv("roBERTa_setup") in ["True", "true", "1"]
bert_setup = os.getenv("bert_setup") in ["True", "true", "1"]

# Webhook 處理流程
def process_webhook(data):
    try:
        # Convert Data
        
        print(data)
        user_input = data["user_input"]
        card_id = data["card_id"]
        checkIsTrello = data["is_trello"]
        fuzzy_sentence = process_sentence(user_input)
        
        if(checkIsTrello):
            try:
                updateDataToCard(card_id, {
                    "name" : f"[進行中] {user_input}",
                    "desc" : f"**關鍵字推薦：** \n\n{fuzzy_sentence}",
                })
            except Exception as exp:
                return {
                    "state" : False,
                    "err_msg" : str(exp),
                    "show_msg" : "[updateDataToCard] 卡片更新失敗",
                }
        
        
        result_of_sentence = process_sentence_to_article_list(user_input,
            setup={
            "limit" : trello_request_limit,
            "anthropic_setup" : anthropic_setup,
            "openai_setup" : openai_setup,
            "roBERTa_setup" : roBERTa_setup,
            "bert_setup" : bert_setup,
        })
        
        if(result_of_sentence['state']):
            # Add Comment
            if(len(result_of_sentence['result']) == 0):
                # Not Find Data so return random message
                commit_msg = random.choice(not_found_msg_list)

                if(checkIsTrello):
                    try:
                        addCommentToCard(card_id, commit_msg)
                        addCoverToCard(card_id,"./static/images/not_found.png")
                    except Exception as exp:
                        return {
                            "state" : False,
                            "err_msg" : str(exp),
                            "show_msg" : "[addCommentToCard] 卡片更新失敗",
                        }
            else:
                #Define String to generate wordcloud
                wc_string = ""

                # Process Result (Send to trello, convert commitmsg)
                for item in reversed(result_of_sentence['result']):
                    # 設定文字雲累加文本(文章內容)
                    wc_string += item['content'] + " "
                    
                    # 設定留言資訊（Answer Core）
                    commit_msg = f"參考資料：\n[{item['title']}]({item['url']})（{item['id']}）\n"
                    if(anthropic_setup):
                        commit_msg += f"參考回答 A ：\n{item['answer_by_anthropic']} \n"
                    if(openai_setup):
                        commit_msg += f"參考回答 C ：\n{item['answer_by_openai']} \n"
                    if(roBERTa_setup):
                        commit_msg += f"參考回答 RB ：\n{item['answer_by_RoBERTa']} \n"
                    if(bert_setup):
                        commit_msg += f"參考回答 B ：\n{item['answer_by_BERT']} \n"
                    
                    if(checkIsTrello):
                        # Add Comment
                        try:
                            # 留言不包含圖片 v1
                            # addCommentToCard(card_id,commit_msg)
                            # 留言包含圖片 v2 up
                            addCommentWithPictureToCard(card_id,f"https://raw.githubusercontent.com/tony13382/trello_helper_img/main/images/{item['id']}.png",commit_msg)
                        except Exception as exp:
                            return {
                                "state" : False,
                                "err_msg" : str(exp),
                                "show_msg" : "[addCommentToCard] 留言失敗",
                            }
                
                # All Done
                try:
                    if(checkIsTrello):
                        # 產生文字雲
                        wc_img_path = generate_wordcloud(wc_string)
                        if(wc_img_path["state"]):
                            # 更新封面
                            addCoverToCard(card_id,wc_img_path["value"])
                        else:
                            return {
                                "state" : False,
                                "err_msg" : wc_img_path["value"],
                                "show_msg" : "[generate_wordcloud] 文字雲產生失敗",
                            }
                except Exception as exp:
                    return {
                        "state" : False,
                        "err_msg" : str(exp),
                        "show_msg" : "[addCoverToCard] 卡片更新失敗",
                    }
            
            return {
                "state" : True,
                "show_msg" : "留言成功",
                "more_info" : {
                    "user_input" : user_input,
                    "searchResult" : result_of_sentence['result'],
                }
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

# 驗證文本是否包含動作關鍵字
def check_action_word(input_string, action_word_list):
    for action_word in action_word_list:
        if action_word in input_string:
            return True
    return False

@app.route('/webhook',methods=['POST','HEAD','GET'])
def webhook_post():
    if request.method == 'POST':
        try:
            req = request.json
            try:
                run_system = False
                # Define to Check Trello Action
                if  "action" in req.keys():
                    if  "type" in req["action"].keys():
                        print("偵測到新增卡片")
                        check_trello_action = True
                        run_system = True
                    else:
                        check_trello_action = False
                        if req["action"] == "api":
                            print("偵測到新調試指令")
                            run_system = True

                if(run_system):
                    
                    if(check_trello_action):
                        user_input = req["action"]["data"]["card"]["name"]
                        card_id = req["action"]["data"]["card"]["id"]
                        #board_id = req["action"]["data"]["board"]["id"]
                    else:
                        user_input = req["user_input"]
                        card_id = req["card_id"]
                    
                    # 檢查是否包含動作關鍵字
                    if(check_action_word(user_input,action_word_list)):
                        # Start to Search and Add Comment
                        process_satae = process_webhook({
                            "user_input" : user_input,
                            "card_id" : card_id,
                            "is_trello" : check_trello_action,
                        })

                        # Add Log to Server
                        if(process_satae['state']):
                            try:
                                updateDataToCard(card_id, {
                                    "name" : f"[已完成] {user_input}",
                                })
                                # Add Success Log
                                add_trello_log(card_id, True, process_satae["show_msg"],more_info=process_satae['more_info'])
                            except Exception as exp:
                                # Add Fail Log(Because of updateDataToCard)
                                add_trello_log(card_id, False, "Card Retitle Error" + "\n\n" + str(exp))
                        else:
                            try:
                                updateDataToCard(card_id, {
                                    "name" : f"[系統有誤] {user_input}",
                                })
                                # Add Fail Log(Because of process_webhook)
                                add_trello_log(card_id, False,process_satae["show_msg"] + "\n\n" + process_satae["err_msg"])
                            except Exception as exp:
                                # Add Fail Log(Because of updateDataToCard)
                                add_trello_log(card_id, False, "Card Retitle Error" + "\n\n" + str(exp))
                    else:
                        print("不包含動作關鍵字: ",user_input)
            except Exception as exp:
                print("Cannot 偵測到新增卡片\n",exp)
                pass
        except:
            print("null Request, It may be a check request")

    return ("", 200)

# Image API(For Trello to Get Image File)
@app.route('/imgs/<filename>')
def serve_image(filename):
    # 構建圖片檔案的路徑
    image_path = f'static/{filename}'
    # 將用戶導向圖片檔案
    return redirect(image_path)

if __name__ == '__main__':
    # Set Debug Mode （每次儲存自動刷新，正式上線需要關閉）
    app.debug = True
    # Run Server on 0.0.0.0 （允許外部連線）
    app.run(host="0.0.0.0",port=flask_server_port)