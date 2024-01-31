import modules.tools.process_words as process_words
import modules.tools.vector_search as vector_search
import modules.tools.mongo_connector as mongo_connector
import modules.tools.vector_search as vector_search
import modules.tools.vector_calc as vector_calculation
import random

# 啟動詞與無資料罐頭訊息載入完成！
import modules.tools.process_words as read_txt_to_list
action_word_list = read_txt_to_list.txt_to_list("./setting/action_word_list.txt")

#############################################
# 關鍵設定數值
Total_tf_value_Gap = 0.01 #文章分數門檻
Limit_Of_Search = 20 #搜尋結果上限
## SBERT 
Sbert_Article_Milvus_Distance = 2.75 #SBERT 搜尋文章相似度門檻
## 權重計算與調整
Mix_Vec_Orginal = 1 #混合向量權重(原始)
Mix_Vec_Inject = 3 #混合向量權重(注入)

#############################################

not_found_msg_list = process_words.txt_to_list("./setting/not_found_msg_list.txt")


def tf(user_input,except_article_ids = []):
    print("開始清理文字")
    query_string = user_input
    #Remove input_string in action_word_list
    for action_word in action_word_list:
        if action_word in query_string:
            query_string = query_string.replace(action_word, "")
    sliced_word_list = process_words.process_sentence(query_string, process_injectionword_setup = False ).split() #只清洗文字
    print(sliced_word_list)
    
    print("開始精準搜尋")
    wc_string = ""
    inprogress_alist = []
    for word in sliced_word_list:
        inprogress_alist.extend(mongo_connector.get_alist_by_kw(word))

    if len(inprogress_alist) == 0:
        return_alist = []
    else:
        # precise_list > 0  有找到文章
        # 如果 article_id 相同則累加 tf_value, 最後根據 tf_value 降冪排序
        # 创建一个字典来存储article_id对应的累加tf_value
        article_tf_values = {}
        
        # 计算累加tf_value
        for item in inprogress_alist:
            article_id = item["article_id"]
            tf_value = item["tf_value"]

            if article_id in article_tf_values:
                article_tf_values[article_id] += tf_value
            else:
                article_tf_values[article_id] = tf_value
        
        # 将字典转换为列表，按照tf_value降序排序
        return_alist = [{"article_id": article_id, "tf_value": tf_value} for article_id, tf_value in sorted(article_tf_values.items(), key=lambda x: x[1], reverse=True) if article_id not in except_article_ids]

    comment_msg = "\n**優先推薦：** \n --- \n\n"
    if len(return_alist) > 0:
        print(f"精準搜尋共 {len(return_alist)} 筆資料")
        
        if len(return_alist) > Limit_Of_Search:
            print(f"優先推薦過多，僅顯示前 {Limit_Of_Search} 筆")
            return_alist = return_alist[:Limit_Of_Search]

        counter = 0
        for article_object in return_alist:
            a_info = mongo_connector.find_article_info(str(article_object["article_id"]))
            if a_info is not None and len(a_info) > 0:
                counter += 1
                comment_msg += f"{counter}. [{a_info['title']}]({a_info['url']})\n"
                wc_string += f'{a_info["cuted"]} '
    else:
        # 精準搜尋沒有結果
        comment_msg += f"精準搜尋沒有結果 \n {random.choice(not_found_msg_list)} \n"
        print("精準搜尋沒有結果")

    print("精準搜尋階段完成")

    return {
        "state" : True,
        "comment_msg" : comment_msg,
        "wc_string" : wc_string,
        "alist" : return_alist,
    }


def sbert(user_input, except_article_ids = []):
    print("SBERT「文章向量加權」算法搜尋開始")
    query_string = user_input
    #Remove input_string in action_word_list
    for action_word in action_word_list:
        if action_word in query_string:
            query_string = query_string.replace(action_word, "")

    return_alist = []
    wc_string = ""
    comment_msg = "\n**你可能也喜歡：**\n --- \n\n"
    # 處理句子
    orginal_sentence = process_words.process_sentence(query_string, process_injectionword_setup = False ) #只清洗文字
    injected_sentence = process_words.process_sentence(query_string) #清洗文字並且進行相似詞搜尋

    # 轉換成向量
    o_vector = process_words.embedding_sentence(orginal_sentence)
    f_vector = process_words.embedding_sentence(injected_sentence)
    q_vector = f_vector #初始化向量


    if(o_vector['state'] and f_vector['state']):
        q_vector["value"] = vector_calculation.calc_array_mean(
            set = [{
                "array" : o_vector['value'],
                "weight" : Mix_Vec_Orginal,
            },{
                "array" : f_vector['value'],
                "weight" : Mix_Vec_Inject,
            }],
            len_array = 768
        )
    else:
        return {
            "state" : False,
            "err_msg" : "向量加權計算失敗",
        }
        

    if q_vector['state']:
        print("向量計算成功")
        fuzzy_search_result = vector_search.search_article_vector(q_vector["value"])
    else:
        return {
            "state" : False,
            "err_msg" : "向量轉換失敗",
        }

    if fuzzy_search_result['state']:
        print("相似文章搜尋成功")
        return_alist = [ x["id"] for x in fuzzy_search_result["value"] if x["distance"] > Sbert_Article_Milvus_Distance and x["id"] not in except_article_ids ]

    else:
        return {
            "state" : False,
            "err_msg" : "相似文章搜尋失敗",
        }
        
    if len(return_alist) > 0:
        print(f"相似文章搜尋共 {len(return_alist)} 筆資料\n")
        if len(return_alist) > Limit_Of_Search:
            print(f"相似文章搜尋結果過多，僅顯示前 {Limit_Of_Search} 筆\n")
            return_alist = return_alist[:Limit_Of_Search]
        # 內容輸出
        counter = 0
        for a_id in return_alist:
            a_info = mongo_connector.find_article_info(a_id)
            if a_info is None:
                continue
            else:
                counter += 1
                comment_msg += f"{counter}. [{a_info['title']}]({a_info['url']})\n" 
                wc_string += f'{a_info["cuted"]} '
                
    else:
        print(f"相似文章搜尋結果為空 \n")
        comment_msg += f"相似文章搜尋沒有結果 \n {random.choice(not_found_msg_list)} \n"   
    
    print("SBERT「文章向量加權」算法搜尋結束")
    return {
        "state" : True,
        "comment_msg" : comment_msg,
        "wc_string" : wc_string,
        "alist" : return_alist,
        "vector_result" : fuzzy_search_result,
    }


def sbert_mix_tf(user_input, except_article_ids = []):
    print("SBERT 算法[sbert]搜尋開始")
    comment_msg = "\n**相關推薦：**\n --- \n\n"
    wc_string = ""
    query_string = user_input
    
    #Remove input_string in action_word_list
    for action_word in action_word_list:
        if action_word in query_string:
            query_string = query_string.replace(action_word, "")

    # 開始注入
    injected_sentence = process_words.process_sentence(query_string, process_injectionword_setup = True )
    print(f"注入文本：{query_string} \n-> {injected_sentence}")
    comment_msg = comment_msg + injected_sentence.replace('\n','')
    # 向量化注入文本
    injected_vector = process_words.embedding_sentence(injected_sentence)
    if injected_vector == False:
        comment_msg = "[sbert.py]SBERT+TF 算法向量化失敗"
        return {
            "state" : False,
            "err_msg" : "[sbert.py]SBERT+TF 算法向量化失敗",
        }

    # 取得相關關鍵字列表 by Milvus
    kwlist_by_m = vector_search.search_keyword_vector(injected_vector["value"])
    if kwlist_by_m["state"] == False:
        comment_msg = "[sbert.py]SBERT+TF 算法(擴展關鍵字)搜尋失敗"
        return {
            "state" : False,
            "err_msg" : "[sbert.py]SBERT+TF 算法(擴展關鍵字)搜尋失敗",
        }

    # 取得相關關鍵字編號
    kwlist_index = [ x["track_id"] for x in kwlist_by_m["value"] ]
    kwlist_str = ""
    for k_id in kwlist_index:
        extra_str = mongo_connector.find_keyword_word(k_id)
        kwlist_str += f"{extra_str} "
        comment_msg += f"、{extra_str}"
    comment_msg += "\n\n"

    # 取得相關關鍵字文章列表
    inject_alist = mongo_connector.get_alist_by_klist(kwlist_index)
    inject_alist = [ x for x in inject_alist if x["total_tf_value"] > Total_tf_value_Gap and x["_id"] not in except_article_ids ]
    
    if len(inject_alist) > 0:
        print(f"SBERT+TF 算法搜尋共 {len(inject_alist)} 筆資料\n")
        if len(inject_alist) > Limit_Of_Search:
            print(f"SBERT+TF 算法搜尋結果過多，僅顯示前 {Limit_Of_Search} 筆\n")
            inject_alist = inject_alist[:Limit_Of_Search]
        # 內容輸出
        counter = 0
        for a_id in inject_alist:
            a_info = mongo_connector.find_article_info(a_id["_id"])
            if a_info is None:
                continue
            else:
                counter += 1
                comment_msg  += f"{counter}. [{a_info['title']}]({a_info['url']})\n"
                wc_string += f'{a_info["cuted"]} '
    else:
        # Not Find Data so return random message
        comment_msg += f"- {random.choice(not_found_msg_list)} \n"
        print("SBERT+TF 算法(擴展關鍵字)搜尋結果為空")


    print("SBERT+TF 算法(擴展關鍵字)搜尋結束")

    return {
        "state" : True,
        "comment_msg" : comment_msg,
        "wc_string" : wc_string,
        "alist" : inject_alist,
    }
    

