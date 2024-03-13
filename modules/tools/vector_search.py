####################################################################
# Setup environment value
####################################################################
import yaml
with open('config.yml', 'r', encoding='utf-8') as config_File:
    config = yaml.safe_load(config_File)

MILVUS_PATH = config['milvus']['path']
MILVUS_PORT = config['milvus']['port']
MILVUS_DB_NAME = config['milvus']['db_name']

RESULT_LIMIT = config["search_filter"]["result_limit_max"]

ARTICLE_COLLECTION = config['milvus']['search_config']['article']['collection_name']
ARTICLE_INDEX_TYPE = config['milvus']['search_config']['article']['index_type']
ARTICLE_METRIC_TYPE = config['milvus']['search_config']['article']['metric_type']

KEYWORD_COLLECTION = config['milvus']['search_config']['keyword']['collection_name']
KEYWORD_INDEX_TYPE = config['milvus']['search_config']['keyword']['index_type']
KEYWORD_METRIX_TYPE = config['milvus']['search_config']['keyword']['metric_type']


SENTENCE_COLLECTION = config['milvus']['search_config']['sentence']['collection_name']
SENTENCE_INDEX_TYPE = config['milvus']['search_config']['sentence']['index_type']
SENTENCE_METRIX_TYPE = config['milvus']['search_config']['sentence']['metric_type']

####################################################################


####################################################################
## Milvus Setup Connection
# Import modules of Milvus
from pymilvus import connections, Collection, utility
# Connect to milvus server (connector)
conn = connections.connect(
    alias="default",
    host=MILVUS_PATH,
    port=MILVUS_PORT,
    db_name=MILVUS_DB_NAME
)
# 設定 Milvus collection 名稱
# 建立 collection
article_collection = Collection(ARTICLE_COLLECTION)
keyword_collection = Collection(KEYWORD_COLLECTION)
sentence_collection = Collection(SENTENCE_COLLECTION)
####################################################################


####################################################################
## 搜尋 Top-K 相似文章
####################################################################
def search_article_vector(query_vector, limit=RESULT_LIMIT, offset=0):
    try:
        # Start searching
        results = article_collection.search(
            data = [query_vector], 
            anns_field = "value", 
            param = {
                "index_type": ARTICLE_INDEX_TYPE,
                "metric_type": ARTICLE_METRIC_TYPE, 
                "params": {"nprobe": 1},      
            },
            limit = limit, 
            offset = offset,
            expr = None,
            # set the names of the fields you want to retrieve from the search result.
            output_fields=['title', 'track_id'],
            consistency_level = "Strong"
        )
        #print(results)
        # get the IDs of all returned hit
        return_array = []
        for hits in results:
            for hit in hits:
                return_array.append({
                    "id" : hit.id,
                    "distance" : hit.distance,
                    "preview" : hit.entity.get('title'),
                    "track_id" : hit.entity.get('track_id'),
                })
        # End of Searching and return the value
        return {
            "state" : True,
            "value" : return_array,
        }
    except Exception as exp:
        return {
            "state" : False,
            "value" : str(exp),
        }
####################################################################


####################################################################  
## 搜尋 Top-K 相似關鍵字
####################################################################
def search_keyword_vector(query_vector, limit=RESULT_LIMIT, offset=0):
    try:
        # Start searching
        results = keyword_collection.search(
            data = [query_vector], 
            anns_field = "vector", 
            param = {
                "index_type": KEYWORD_INDEX_TYPE,
                "metric_type": KEYWORD_METRIX_TYPE, 
                "params": {"nprobe": 1},      
            },
            limit = limit, 
            offset = offset,
            expr = None,
            # set the names of the fields you want to retrieve from the search result.
            output_fields=['preview_str', 'link_id'],
            consistency_level = "Strong"
        )
        print(results)
        # get the IDs of all returned hit
        return_array = []
        for hits in results:
            for hit in hits:
                return_array.append({
                    "id" : hit.id,
                    "distance" : hit.distance,
                    "preview" : hit.entity.get('preview_str'),
                    "track_id" : hit.entity.get('link_id'),
                })
        # End of Searching and return the value
        return {
            "state" : True,
            "value" : return_array,
        }
    except Exception as exp:
        return {
            "state" : False,
            "value" : str(exp),
        }
####################################################################
    

####################################################################
## 搜尋 Top-K 相似句子
####################################################################
def search_sentence_vector(query_vector, limit=RESULT_LIMIT, offset=0):
    try:
        # Start searching
        results = sentence_collection.search(
            data = [query_vector], 
            anns_field = "vector", 
            param = {
                "index_type": SENTENCE_INDEX_TYPE,
                "metric_type": SENTENCE_METRIX_TYPE, 
                "params": {"nprobe": 1},      
            },
            limit = limit, 
            offset = offset,
            expr = None,
            # set the names of the fields you want to retrieve from the search result.
            output_fields=['sentence', 'article_id','token_size'],
            consistency_level = "Strong"
        )
        #print(results)
        # return the value
        return_array = []
        for hits in results:
            for hit in hits:
                return_array.append({
                    "distance" : hit.distance,
                    "preview" : hit.entity.get('sentence'),
                    "track_id" : hit.entity.get('article_id'),
                    "token_size" : hit.entity.get('token_size'),
                })
        # End of Searching and return the value
        return {
            "state" : True,
            "value" : return_array,
        }
    except Exception as exp:
        return {
            "state" : False,
            "value" : str(exp),
        }
####################################################################