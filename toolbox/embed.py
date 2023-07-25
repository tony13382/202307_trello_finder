# Import modules
from sentence_transformers import SentenceTransformer, util

# Select model by transformer
# about model: https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2
sbert_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
print('sbert_model loaded')


## 轉換文本至向量
def embedding_sentence(sentence):
    ####################
    # Request Value
    # sentence : String
    #-------------------
    # Response Value
    # state : Boolean
    # value : [] Array(768)
    ####################
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
