# Import modules of Milvus
from pymilvus import connections, Collection, utility
# Setup environment value
import os
from dotenv import load_dotenv
load_dotenv()
milvus_path = os.getenv("milvus_path")
milvus_port = os.getenv("milvus_port")
milvus_db_name = os.getenv("milvus_db_name")

milvus_article_collection = os.getenv("milvus_article_collection")
article_vector_index_type = os.getenv("article_vector_index_type")
article_vector_metric_type = os.getenv("article_vector_metric_type")

milvus_keyword_collection = os.getenv("milvus_keyword_collection")
keyword_vector_index_type = os.getenv("keyword_vector_index_type")
keyword_vector_metric_type = os.getenv("keyword_vector_metric_type")


# Connect to milvus server (connector)
conn = connections.connect(
    alias="default",
    host=milvus_path,
    port=milvus_port,
    db_name=milvus_db_name
)

# 設定 Milvus collection 名稱
# 建立 collection
article_collection = Collection(milvus_article_collection)
keyword_collection = Collection(milvus_keyword_collection)


## 搜尋 Top-K 相似文本
def search_article_vector(query_vector, limit=10, offset=0):
    try:
        # Start searching
        results = article_collection.search(
            data = [query_vector], 
            anns_field = "value", 
            param = {
                "index_type": article_vector_index_type,
                "metric_type": article_vector_metric_type, 
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
    
## 搜尋 Top-K 相似關鍵字
def search_keyword_vector(query_vector, limit=10, offset=0):
    try:
        # Start searching
        results = keyword_collection.search(
            data = [query_vector], 
            anns_field = "vector", 
            param = {
                "index_type": keyword_vector_index_type,
                "metric_type": keyword_vector_metric_type, 
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