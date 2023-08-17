# coding:utf-8
import ast # 用於將字串轉換成串列
import re

from flask import Flask
from flask import render_template, jsonify, redirect
from flask import request

# 用於隨機抽取回應（無答案時）
import random

####################################################################
# Setup environment value
####################################################################


import os
from dotenv import load_dotenv
load_dotenv()
distance_filter = float(os.getenv("distance_filter"))
flask_server_port = int(os.getenv("flask_server_port"))
# Webhook API
trello_request_limit = int(os.getenv("trello_request_limit"))
# Get Environment Value
anthropic_setup = os.getenv("anthropic_setup") in ["True", "true", "1"]
openai_setup = os.getenv("openai_setup") in ["True", "true", "1"]
roBERTa_setup = os.getenv("roBERTa_setup") in ["True", "true", "1"]
bert_setup = os.getenv("bert_setup") in ["True", "true", "1"]


# 讀取文字檔並轉換成串列
def txt_to_list(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.readlines()
            content = [line.strip() for line in content]
        return content
    except FileNotFoundError:
        print("找不到指定的檔案。請檢查檔案路徑是否正確。", file_path)
        return []
    except Exception as e:
        print("讀取檔案時發生錯誤：", e)
        return []

# 指定文字檔路徑
file_path = 'your_file.txt'  # 請替換成實際的檔案路徑
action_word_list = txt_to_list("./setting/action_word_list.txt")
not_found_msg_list = txt_to_list("./setting/not_found_msg_list.txt")
print("啟動詞與無資料罐頭訊息載入完成！")


####################################################################
# Process Module
####################################################################


# SBERT 編碼模組
from modules.tools.process_words import embedding_sentence, process_sentence, generate_wordcloud
import modules.tools.process_words as process_words
# Milvus 向量搜尋與運算模組
from modules.tools.vector_search import search_article_vector
import modules.tools.vector_search as vector_search
# MongoDB 文章搜尋模組
from modules.tools.mongo_connector import find_article_info, add_trello_log
import modules.tools.mongo_connector as mongo_connector
# GPT 回答模組
from modules.tools.answer_core import qa_by_anthropic, qa_by_openai, qa_by_RoBERTa, qa_by_bert
# Trello 模組
from modules.tools.trello_connector import updateDataToCard, addCommentToCard, addCommentWithPictureToCard, addCoverToCard
import modules.tools.trello_connector as trello_connector
# Vector 計算模組
import modules.tools.vector_calc as vector_calculation



# 預處理 Milvus 回傳的資料
def process_milvus_result(req_array, sentence ,anthropic_setup=False,openai_setup=False,roBERTa_setup=False,bert_setup=False):
    return_array = []
    for item in req_array:
        # IF distance < 設定值, break and return 相關性不足的文章
        if(item['distance'] < distance_filter):
            break

        # Use track_id to find Ariicle (Only one article)
        article_id = item['track_id']
        article = find_article_info(article_id)
        if article is not None:
            insert_data = {
                "id" : item['id'],
                "distance" : item['distance'],
                "title" : article['title'],
                "url" : article['url'],
                "content" : article['content'],
            }
            # Use Meta's content to answer question by gpt
            if anthropic_setup:
                answer = qa_by_anthropic(article['content'], sentence)
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
                answer = qa_by_openai(article['content'], sentence)
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
                answer = qa_by_RoBERTa(article['content'], sentence)
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
                answer = qa_by_bert(article['content'], sentence)
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
            print(article, "cannot find")
        
        return_array.append(insert_data)

    # End of Combine amd return the value
    return {
        "state" : True,
        "result" : return_array,
    }

def process_sentence_to_article_list(sentence,setup):
    # 處理句子
    orginal_sentence = process_sentence(sentence, process_injectionword_setup = False ) #只清洗文字
    fuzzy_sentence = process_sentence(sentence) #清洗文字並且進行相似詞搜尋
    
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
        result = search_article_vector(q_vector["value"], limit=limit, offset=offset)
        
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
                "show_msg" : "系統模組（search_article_vector）失敗，請聯絡工程人員",
                "error_code" : 501,
            }
    else:
        return {
            "state" : False,
            "err_msg" : q_vector["value"],
            "show_msg" : "模組失敗，請聯絡工程人員",
            "error_code" : 501,
        }

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
                            addCommentWithPictureToCard(card_id,f"https://raw.githubusercontent.com/tony13382/trello_helper_img_w/main/{item['id']}.png",commit_msg)
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

def check_is_done(input_string):
    if "[已完成]" in input_string:
        return True
    else:
        return False
############################################################################################################################
# webhook3.0 結果算法
############################################################################################################################

def get_article_index_list_precise(wordlist):
    precise_article_list = []
    for word in wordlist:
        precise_article_list.extend(mongo_connector.get_alist_by_kw(word))
    
    if len(precise_article_list) == 0:
        return []
    
    # precise_list > 0  有找到文章
    # 如果 article_id 相同則累加 score, 最後根據 score 降冪排序
    # 创建一个字典来存储article_id对应的累加score
    article_scores = {}
    
    # 计算累加score
    for item in precise_article_list:
        article_id = item["article_id"]
        score = item["score"]
        if article_id in article_scores:
            article_scores[article_id] += score
        else:
            article_scores[article_id] = score
    
    # 将字典转换为列表，按照score降序排序
    return [{"article_id": article_id, "score": score} for article_id, score in sorted(article_scores.items(), key=lambda x: x[1], reverse=True)]


def webhook_v3_engine(user_input,card_id,checkIsTrello = False):
    
    # 定義需要留言的組件
    wc_string = ""
    return_data = {}

    # 驗證文本是否包含動作關鍵字
    if check_action_word(user_input, action_word_list) is True and check_is_done(user_input) is False:
        # 文本包含動作關鍵字
        # 開始清理文字
        if checkIsTrello is True:
            trello_connector.updateDataToCard(card_id, {
                "name" : f"[進行中] {user_input}",
            })
        

        #################################################################################
        #################################################################################
        
        # 開始文本注入搜尋
        print("開始文本注入搜尋")
        comment_injected_msg = "**創意搜尋結果：**\n --- \n\n"
        wc_string_injected = ""

        # 開始注入
        injected_sentence = process_words.process_sentence(user_input, process_injectionword_setup = True )
        print(f"注入文本：{user_input} \n-> {injected_sentence}")
        comment_injected_msg += f"{injected_sentence} \n---\n"
        # 向量化注入文本
        injected_vector = process_words.embedding_sentence(injected_sentence)
        if injected_vector == False:
            print("文本注入向量化失敗")
        else:
            # 取得相關關鍵字列表 by Milvus
            kwlist_by_m = vector_search.search_keyword_vector(injected_vector["value"])

        if kwlist_by_m["state"] == False:
            print("文本注入搜尋失敗")
        else:
            # 取得相關關鍵字編號
            kwlist_index = [ x["track_id"] for x in kwlist_by_m["value"] ]
            # 取得相關關鍵字文章列表
            inject_alist = mongo_connector.get_alist_by_klist(kwlist_index)
            inject_alist = [ x for x in inject_alist if x["total_score"] > 0.05 ]
            
            if len(inject_alist) > 0:
                print(f"文本注入搜尋共 {len(inject_alist)} 筆資料")
                if len(inject_alist) > 20:
                    print("文本注入搜尋結果過多，僅顯示前 20 筆")
                    inject_alist = inject_alist[:20]
                # 內容輸出
                counter = 0
                for a_id in inject_alist:
                    a_info = mongo_connector.find_article_info(a_id["_id"])
                    if a_info is None:
                        continue
                    else:
                        counter += 1
                        comment_injected_msg  += f"{counter}. [{a_info['title']}]({a_info['url']}) \n"
                        wc_string += f'{a_info["cuted"]} '
                        wc_string_injected += f'{a_info["cuted"]} '
            else:
                comment_injected_msg += f"- 精準搜尋沒有結果 \n"
                print("文本注入搜尋結果為空")
        
        return_data["injected"] = {
            "msg" : comment_injected_msg,
            "alist" : inject_alist,
        }

        if checkIsTrello is True:
            # 輸出留言
            trello_connector.addCommentToCard(
                card_id, 
                comment_injected_msg
            )
            # 產生文字雲
            if len(inject_alist) > 0:
                wc_img_path_injected = process_words.generate_wordcloud(wc_string_injected, f"創意搜尋文字雲")
                if wc_img_path_injected["state"] is True:
                    trello_connector.addFileToCard(
                        card_id,
                        wc_img_path_injected["value"]
                    )


        #################################################################################
        #################################################################################

        # 開始文章文本模糊搜索
        print("開始文章文本模糊搜索")
        
        fuzzy_search_alist = []
        wc_string_fuzzy = ""
        comment_fuzzy_msg = "**相似搜尋結果：**\n --- \n\n"
        # 處理句子
        orginal_sentence = process_words.process_sentence(user_input, process_injectionword_setup = False ) #只清洗文字
        injected_sentence = process_words.process_sentence(user_input) #清洗文字並且進行相似詞搜尋

        # 轉換成向量
        o_vector = process_words.embedding_sentence(orginal_sentence)
        f_vector = process_words.embedding_sentence(injected_sentence)
        q_vector = f_vector


        ## 權重計算與調整
        orginal_weight = 1
        fuzzy_weight = 3


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
            print("向量轉換失敗")

        if q_vector['state']:
            print("向量計算成功")
            fuzzy_search_result = vector_search.search_article_vector(q_vector["value"])

        if fuzzy_search_result['state']:
            print("相似文章搜尋成功")
            fuzzy_search_alist = [ x["id"] for x in fuzzy_search_result["value"] if x["distance"] > 2.75 ]
            
        if len(fuzzy_search_alist) > 0:
            print(f"相似文章搜尋共 {len(fuzzy_search_alist)} 筆資料")  
            if len(fuzzy_search_alist) > 20:
                print("相似文章搜尋結果過多，僅顯示前 20 筆")
                fuzzy_search_alist = fuzzy_search_alist[:20]
            # 內容輸出
            counter = 0
            for a_id in fuzzy_search_alist:
                a_info = mongo_connector.find_article_info(a_id)
                if a_info is None:
                    continue
                else:
                    counter += 1
                    comment_fuzzy_msg += f"{counter}. [{a_info['title']}]({a_info['url']}) \n" 
                    wc_string += f'{a_info["cuted"]} '
                    wc_string_fuzzy += f'{a_info["cuted"]} '
        else:
            comment_fuzzy_msg += f"相似文章搜尋沒有結果 \n"   
            print("相似文章搜尋結果為空")

        return_data["fuzzy"] = {
            "msg" : comment_fuzzy_msg,
            "alist" : fuzzy_search_alist,
        }

        if checkIsTrello is True:
            # 輸出留言
            trello_connector.addCommentToCard(
                card_id, 
                comment_fuzzy_msg
            )
            # 產生文字雲
            if len(fuzzy_search_alist) > 0:
                wc_img_path_fuzzy = process_words.generate_wordcloud(wc_string_fuzzy, f"相似搜尋文字雲")
                if wc_img_path_fuzzy["state"] is True:
                    trello_connector.addFileToCard(
                        card_id,
                        wc_img_path_fuzzy["value"]
                    )
        
        print("文章文本模糊搜索結束")


        #################################################################################
        #################################################################################

        print("開始清理文字")
        sliced_word_list = process_words.process_sentence(user_input, process_injectionword_setup = False ).split() #只清洗文字
        print(sliced_word_list)
        print("開始精準搜尋")

        wc_string_precise = ""

        # 開始精準搜尋
        precise_result = get_article_index_list_precise(sliced_word_list)

        comment_precise_msg = "**精準搜尋結果：** \n --- \n\n"
        if len(precise_result) == 0:
            # 精準搜尋沒有結果
            comment_precise_msg += f"精準搜尋沒有結果 \n"
            print("精準搜尋沒有結果")
        else:
            
            print(f"精準搜尋共 {len(precise_result)} 筆資料")
            
            if len(precise_result) > 20:
                print("精準搜尋結果過多，僅顯示前 20 筆")
                precise_result = precise_result[:20]

            counter = 0
            for article_object in precise_result:
                article_info = mongo_connector.find_article_info(str(article_object["article_id"]))
                if article_info is not None and len(article_info) > 0:
                    counter += 1
                    comment_precise_msg += f"{counter}. [{article_info['title']}]({article_info['url']}) \n"
                    wc_string += f'{article_info["cuted"]} '
                    wc_string_precise += f'{article_info["cuted"]} '
            
        return_data["precise"] = {
            "msg" : comment_precise_msg,
            "alist" : precise_result,
        }
        
        print("精準搜尋階段完成")

        if checkIsTrello is True:
            # 輸出留言
            trello_connector.addCommentToCard(
                card_id, 
                comment_precise_msg
            )
            # 產生文字雲
            if len(precise_result) > 0:
                wc_img_path = process_words.generate_wordcloud(wc_string_precise, f"精準搜尋文字雲")
                if wc_img_path["state"] is True:
                    trello_connector.addFileToCard(
                        card_id,
                        wc_img_path["value"]
                    )


        #################################################################################
        #################################################################################


        if checkIsTrello is True:
            # 產生文字雲
            wc_img_path = process_words.generate_wordcloud(wc_string, f"綜合文字雲")
            if(wc_img_path["state"]):
                trello_connector.addCommentToCard(
                    card_id, 
                    "---"
                )
                # 更新封面
                print("WordCloud 圖片產生成功")
                trello_connector.addCoverToCard(card_id,wc_img_path["value"])

            trello_connector.updateDataToCard(card_id, {
                "name" : f"[已完成] {user_input}",
            })

        print("搜索結束")

        return return_data


####################################################################
# API Server
####################################################################

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
        result = search_article_vector(q_vector, limit=limit)
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


@app.route('/webhook2',methods=['POST','HEAD','GET'])
def webhook_post():
    if request.method == 'POST':
        try:
            # Get Request Data
            req = request.json
            try:
                run_system = False
                # Define to Check Trello Action
                
                if  "action" in req.keys():
                    if  "type" in req["action"].keys():
                        check_trello_action = True
                        print("偵測到 Trello Action",req["action"]["type"])
                        if(req["action"]["type"] == "createCard"):
                            print("偵測到新增卡片")
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

@app.route('/webhook3',methods=['POST','HEAD','GET'])
def webhook_v3_post():
    if request.method == 'POST':
        try:
            # Get Request Data
            req = request.json
            try:
                run_system = False
                # Define to Check Trello Action
                
                if  "action" in req.keys():
                    if  "type" in req["action"].keys():
                        check_trello_action = True
                        print("偵測到 Trello Action",req["action"]["type"])
                        if(req["action"]["type"] == "createCard"):
                            print("偵測到新增卡片")
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
                        try:
                            run = webhook_v3_engine(user_input,card_id,check_trello_action)
                            mongo_connector.add_trello_log(
                                card_id = card_id, 
                                state = True, 
                                msg = "留言成功", 
                                more_info=run
                            )
                            return ("", 200)
                        except Exception as exp:
                            mongo_connector.add_trello_log(
                                card_id = card_id, 
                                state = False, 
                                msg= "v3_engine Error" + "\n\n" + str(exp)
                            )
                            return ("", 200)
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