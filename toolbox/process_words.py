# Import modules
from sentence_transformers import SentenceTransformer, util


# Import modules of wordCut
import re
import monpa
monpa.load_userdict("./docs/process_words_monpa_dict.txt")

# Import modules of mongo_connector(For close_word_search)
from toolbox.mongo_connector import close_word_search

# Select model by transformer
# about model: https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2
sbert_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
print('sbert_model loaded')

####################
## 轉換文本至向量
# Request Value
# sentence : String
#-------------------
# Response Value
# state : Boolean
# value : [] Array(768)
####################
def embedding_sentence(sentence):
    try:
        return {
            "state" : True,
            "value" : sbert_model.encode(sentence).tolist(), # return a vector list
        }
    except Exception as exp:
        return {
            "state" : False,
            "value" : str(exp),
        }

def process_sentence(sentence):
    # 1. 去除標點符號
    # 使用正则表达式匹配标点符号，并将其替换为空字符串
    # \p{P} 表示 Unicode 标点符号
    # \s 表示 Unicode 空白字符（包括空格、制表符、换行符等）
    # + 表示匹配一个或多个连续的标点符号或空白字符
    sentence = re.sub(r'[^\w\s]', '', sentence)

    # 2. 去除停用词
    # 停用词表 ＃為基礎少數通用詞彙 ＃速度慢
    stop_word_list = ["是什麼", "小幫手我想問", "我想問", "小幫手我想知道"]
    for stop_word in stop_word_list:
        sentence = sentence.replace(stop_word, "")
    
    # 3. 将句子切割成词
    word_list = monpa.cut(sentence)
    
    # 4. 去除停用词並套用 close_word_search
    word_list = [close_word_search(word) for word in word_list]

    # 将词列表拼接成句子
    sentence = ' '.join(word_list)
    return sentence