import modules.tools.process_words as process_words
import modules.tools.vector_search as vector_search
import modules.tools.mongo_connector as mongo_connector
import modules.tools.vector_search as vector_search
import modules.tools.vector_calc as vector_calculation
import random

# 啟動詞與無資料罐頭訊息載入完成！
import modules.tools.process_words as read_txt_to_list
action_word_list = read_txt_to_list.txt_to_list("./setting/action_word_list.txt")
confuse_list = process_words.txt_to_list("./setting/confuse_word.txt")
#############################################
# 關鍵設定數值
#############################################
import yaml
with open('config.yml', 'r', encoding='utf-8') as config_File:
    config = yaml.safe_load(config_File)

Min_of_tf = config["search_filter"].get("tf_score_min", 0.01) #文章分數門檻
Limit_Of_Search = config["search_filter"].get("result_limit_max", 20) #搜尋結果上限
## SBERT 
Sbert_Article_Milvus_Distance = config["search_filter"].get("sbert_article_distence_min", 2.75) #SBERT 搜尋文章相似度門檻
print(f"SBERT 搜尋文章相似度門檻：{Sbert_Article_Milvus_Distance}")
## 權重計算與調整
Mix_Vec_Orginal = config["search_filter"]["weight_of_vector"].get("original", 1) #混合向量權重(原始)
Mix_Vec_Inject = config["search_filter"]["weight_of_vector"].get("injection", 3) #混合向量權重(注入)
#############################################


#############################################
# 去除干擾文字
#############################################
#- 去除易干擾文字
def remove_confuse_word(input_string):
    for word in confuse_list:
        input_string = input_string.replace(word , "")
    return input_string
#- 去除易干擾文字列表(含重組功能)
def remove_confuse_wlist(wlist):
    # 建立一個新的 list 來存放處理後的結果
    return_list = []
    for index in range(len(wlist)):
        # 如果 wlist[index] 不在 confuse_list 中，則加入 return_list
        if wlist[index] not in confuse_list:
            return_list.append(wlist[index])
        else:
            # 如果 wlist[index] 在 confuse_list 中，且不是第一個元素，則將 wlist[index-1]+易干擾文字 加入 return_list
            if index > 0:
                return_list.append(wlist[index-1]+wlist[index])
    return return_list
#############################################


#############################################
# 生成 Comment Message
#############################################
# 載入罐頭訊息
not_found_msg_list = process_words.txt_to_list("./setting/not_found_msg_list.txt")
# 生成 Comment Message
def generate_comment_msg(alist = None, comment_title = "", note = ""):
    # Set Comment Title
    if comment_title == "":
        comment_title = "推薦資料"
    comment_msg = f"\n**{comment_title}：**\n --- \n\n"
    # If alist is None alist=[]
    if alist is None:
        alist = []
    # If alist is empty return not found message
    if len(alist) == 0:
        comment_msg += f"- {comment_title}沒有結果：{random.choice(not_found_msg_list)} \n"
    else:
        # 預覽資料量
        print(f"{comment_title}共 {len(alist)} 筆資料")
        # 如果資料量過多，僅顯示前 Limit_Of_Search 筆
        if len(alist) > Limit_Of_Search:
            print(f"{comment_title}過多，僅顯示前 {Limit_Of_Search} 筆")
            alist = alist[:Limit_Of_Search]
        # 定義計數器生成 Comment Message
        counter = 0
        # 生成 Comment Message 文章列表
        for article_id in alist:
            # 取得文章資訊
            a_info = mongo_connector.find_article_info(str(article_id))
            # 如果文章資訊不為空，則加入 | 標號. [標題](連結)
            if a_info is not None and len(a_info) > 0:
                counter += 1
                #comment_msg += f"{counter}. [{a_info['title']}]({a_info['url']}) \[編號：{a_info['link_id']}\] \n"
                comment_msg += f"{counter}. [{a_info['title']}]({a_info['url']}) \n"
    # 如有有備註則加入 footer msg 分隔線＋備註
    if len(note) != 0:
        comment_msg += f"\n --- \n{note}\n"
    # 回傳 Comment Message
    return comment_msg
#############################################


#############################################
# 生成 WordCloud String
#############################################
def generate_wordcloud_string(alist = None , original_string = ""):
    # If alist is None alist=[]
    if alist is None:
        alist = []
    # If alist is empty return original string
    if len(alist) == 0:
        return original_string
    else:
        wc_string = ""
        for article_id in alist:
            a_info = mongo_connector.find_article_info(str(article_id))
            if a_info is not None and len(a_info) > 0:
                wc_string += f'{a_info["cutted"]} '
        return wc_string
#############################################


#############################################
# 搜尋引擎
#############################################
# TF 搜尋引擎
def tf(user_input,except_article_ids = []):
    print("開始清理文字")
    # Remove input_string in action_word_list
    query_string = process_words.clean_action_word(user_input)
    # 清洗文本成關鍵字列表
    query_wlist = process_words.process_sentence(query_string, process_injectionword_setup = False ).split() #只清洗文字
    # 去除易干擾文字
    query_wlist = remove_confuse_wlist(query_wlist)
    print(query_wlist)
    print("開始精準搜尋")
    # 定義一個空的 alist 來存放搜尋結果
    inprogress_alist = []
    for word in query_wlist:
        # 將每個關鍵字的搜尋結果加入 inprogress_alist
        inprogress_alist.extend(mongo_connector.get_alist_by_kw(word))
    # 如果 inprogress_alist 為空，則 return_alist = []
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
            # 如果 article_id 已经在字典中，则累加 tf_value
            if article_id in article_tf_values:
                article_tf_values[article_id] += tf_value
            else:
                # 如果 article_id 不在字典中，则添加新的键值对
                article_tf_values[article_id] = tf_value
        # 将字典转换为列表，按照tf_value降序排序
        return_alist = [{"article_id": article_id, "tf_value": tf_value} for article_id, tf_value in sorted(article_tf_values.items(), key=lambda x: x[1], reverse=True) if tf_value > Min_of_tf and article_id not in except_article_ids]
    # 生成 trello comment
    if len(return_alist) > 0:
        # 生成 trello comment
        comment_msg = generate_comment_msg(
            alist = [id["article_id"] for id in return_alist], 
            comment_title = "精準搜尋")
        # 生成 wordcloud string
        wc_string = generate_wordcloud_string(
            alist = [id["article_id"] for id in return_alist], 
            original_string = "")
    else:
        # 生成 trello comment
        comment_msg = generate_comment_msg(
            comment_title="精準搜尋")
        # 生成 wordcloud string
        wc_string = ""
    # 回傳結果
    print("精準搜尋階段完成")
    return {
        "state" : True,
        "comment_msg" : comment_msg,
        "wc_string" : wc_string,
        "alist" : return_alist,
    }
#------------------------------------------------

#------------------------------------------------
# SBERT 搜尋引擎
def sbert(user_input, except_article_ids = []):
    print("SBERT「文章向量加權」算法搜尋開始")
    # Remove input_string in action_word_list
    query_string = process_words.clean_action_word(user_input)
    return_alist = []
    # 處理句子
    # 去除易干擾文字
    query_string = remove_confuse_word(query_string)
    # 斷詞與清理
    orginal_sentence = process_words.process_sentence(query_string, process_injectionword_setup = False ) #只清洗文字
    print(f"原始句子：{orginal_sentence}")
    # 斷詞＋注入文字
    injected_sentence = process_words.process_sentence(query_string, process_injectionword_setup = True) #清洗文字並且進行相似詞搜尋
    print(f"注入句子：{injected_sentence}")
    # 轉換原始文本成向量 (再次去除易干擾文字)
    original_vector = process_words.embedding_sentence(remove_confuse_word(orginal_sentence))
    # 轉換注入文本成向量 (再次去除易干擾文字)
    injected_vector = process_words.embedding_sentence(remove_confuse_word(injected_sentence))
    # 初始化搜尋用向量
    query_vector = injected_vector #初始化向量
    if(original_vector['state'] is True and injected_vector['state'] is True):
        # 初始化狀態
        query_vector["state"] = False
        # 向量加權計算重新賦值給 query_vector
        query_vector["value"] = vector_calculation.calc_array_mean(
            set = [{
                "array" : original_vector['value'],
                "weight" : Mix_Vec_Orginal,
            },{
                "array" : injected_vector['value'],
                "weight" : Mix_Vec_Inject,
            }],
            len_array = 768
        )
        # 刷新狀態
        query_vector["state"] = True
    else:
        return {
            "state" : False,
            "err_msg" : "向量加權計算失敗",
        }
    if query_vector['state'] is True:
        print("向量計算成功")
        # 進行相似文章搜尋
        fuzzy_search_result = vector_search.search_article_vector(query_vector["value"])
    else:
        return {
            "state" : False,
            "err_msg" : "向量轉換失敗",
        }
    if fuzzy_search_result['state'] is True:
        print("相似文章搜尋成功")
        # 取得相似文章 ID 列表
        return_alist = [ x["id"] for x in fuzzy_search_result["value"] if x["distance"] > Sbert_Article_Milvus_Distance and x["id"] not in except_article_ids ]
    else:
        return {
            "state" : False,
            "err_msg" : "相似文章搜尋失敗",
        }
    # 生成 trello comment
    comment_msg = generate_comment_msg(
        alist = return_alist,
        comment_title = "你可能也喜歡")
    # 生成 wordcloud string
    genarate_wordcloud_string = generate_wordcloud_string(
        alist = return_alist,
        original_string = "")
    # 回傳結果
    print("SBERT「文章向量加權」算法搜尋結束")
    return {
        "state" : True,
        "comment_msg" : comment_msg,
        "wc_string" : genarate_wordcloud_string,
        "alist" : return_alist,
        "vector_result" : fuzzy_search_result,
        'query' : {
            "orginal_sentence" : orginal_sentence,
            "injected_sentence" : injected_sentence,
            "orginal_vector" : original_vector["value"],
            "injected_vector" : injected_vector["value"].tolist(),
            "query_vector" : query_vector["value"].tolist(),
        },
    }
#------------------------------------------------

#------------------------------------------------
# SBERT+TF 混合搜尋引擎
def sbert_mix_tf(user_input, except_article_ids = []):
    print("SBERT 算法[sbert]搜尋開始")
    # Remove input_string in action_word_list
    query_string = process_words.clean_action_word(user_input)
    # 開始注入 > Remove 常見干擾文字 | 避免易干擾字進入向量計算
    injected_sentence = remove_confuse_word(process_words.process_sentence(query_string, process_injectionword_setup = True ))
    print(f"注入文本：{query_string} \n-> {injected_sentence}")
    # 備註轉換文字
    comment_note = injected_sentence.replace('\n','')
    # 向量化注入文本
    injected_vector = process_words.embedding_sentence(injected_sentence)
    # 如果向量化失敗則回傳錯誤
    if injected_vector == False:
        return {
            "state" : False,
            "err_msg" : "[sbert.py]SBERT+TF 算法向量化失敗",
        }
    # 取得相關關鍵字列表 by Milvus
    kwlist_by_m = vector_search.search_keyword_vector(injected_vector["value"])
    # 如果關鍵字搜尋失敗則回傳錯誤
    if kwlist_by_m["state"] == False:
        return {
            "state" : False,
            "err_msg" : "[sbert.py]SBERT+TF 算法(擴展關鍵字)搜尋失敗",
        }
    # 取得相關關鍵字編號
    kwlist_index = [ x["track_id"] for x in kwlist_by_m["value"] ]
    # 取得關鍵字列表
    kwlist_str = ""
    for k_id in kwlist_index:
        extra_str = mongo_connector.find_keyword_word(k_id)
        kwlist_str += f"{extra_str} "
        comment_note += f"、{extra_str}"
    comment_note += "\n\n"
    # 利用關鍵字文取得章列表
    inject_alist = mongo_connector.get_alist_by_klist(kwlist_index)
    inject_alist = [ x for x in inject_alist if x["total_tf_value"] > Min_of_tf and x["_id"] not in except_article_ids ]
    # 生成 trello comment
    comment_note = generate_comment_msg(
        alist = [id["_id"] for id in inject_alist],
        comment_title = "相關推薦",
        note = comment_note)
    # 生成 wordcloud string
    wc_string = generate_wordcloud_string(
        alist = [id["_id"] for id in inject_alist],
        original_string = "")
    # 回傳結果
    print("SBERT+TF 算法(擴展關鍵字)搜尋結束")
    return {
        "state" : True,
        "comment_msg" : comment_note,
        "wc_string" : wc_string,
        "alist" : inject_alist,
    }
#------------------------------------------------
#############################################