# Import modules
from sentence_transformers import SentenceTransformer, util


# Import modules of wordCut
# https://github.com/monpa-team/monpa
# 正體中文斷詞系統應用於大型語料庫之多方評估研究: https://aclanthology.org/2022.rocling-1.24.pdf
import re
import monpa
monpa.load_userdict("./docs/MONPA_斷詞字典.txt")
print('monpa_dict loaded')


# Import modules of wordCloud
import matplotlib.pyplot as plt
from wordcloud import WordCloud


# Import modules of mongo_connector(For process_sentence)
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


####################
## 整理文本並注入資料
# Request Value
# sentence : String
#-------------------
# Response Value
# => String
####################
def process_sentence(sentence):
    # 1. 去除標點符號
    # 使用正则表达式匹配标点符号，并将其替换为空字符串
    # \p{P} 表示 Unicode 标点符号
    # \s 表示 Unicode 空白字符（包括空格、制表符、换行符等）
    # + 表示匹配一个或多个连续的标点符号或空白字符
    sentence = re.sub(r'[^\w\s]', '', sentence)

    # 2. 去除停用词
    # 停用词表 ＃為基礎少數通用詞彙 ＃速度慢
    stop_word_list = ["是什麼", "什麼是", "小幫手我想問", "我想問", "小幫手我想知道", "請問", "的原理", "常數", "係數"]
    for stop_word in stop_word_list:
        sentence = sentence.replace(stop_word, "")
    
    # 3. 将句子切割成词
    word_list = monpa.cut(sentence)
    
    # 4. 去除停用词並套用 close_word_search
    word_list = [close_word_search(word) for word in word_list]

    # 将词列表拼接成句子
    sentence = ' '.join(word_list)
    return sentence


####################
## 生成文字雲
# Request Value
# input_string : String
#-------------------
# Response Value
# state : Boolean
# value : String 圖片路徑
####################

# Function to load stop words from the file
def load_stopwords(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        stopwords = set(file.read().split())
    return stopwords

# Load Chinese stop words
stopwords_file = "docs/stopwords_chinese.txt"
stopwords = load_stopwords(stopwords_file)
print("Load Chinese stop words Done")

# Generate a word cloud image
chinese_font_path = "docs/jf-openhuninn-2.0.ttf"
print("Load Chinese font Done")

def generate_wordcloud(input_string, filename="ram"):
    try:
        # Process the input string
        words = monpa.cut(input_string)
        wc_string = " ".join(w for w in words if w not in stopwords)
        
        # Generate a word cloud image
        wordcloud = WordCloud(
            background_color="white",
            width=600,
            height=400,
            margin=3,
            font_path=chinese_font_path,
            prefer_horizontal=1,
            colormap="Set2",
            stopwords=stopwords,  # Pass the loaded stop words
        ).generate(wc_string)
        plt.switch_backend('Agg')
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        save_path = f"static/images/wordCloud/{filename}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.clf()
        return {
            "state" : True,
            "value" : save_path,
        }
    except Exception as exp:
        print(exp)
        return {
            "state" : False,
            "value" : str(exp),
        }