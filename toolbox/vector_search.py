# Import modules of Milvus
from pymilvus import connections, Collection, utility
# Setup environment value
import os
from dotenv import load_dotenv
load_dotenv()
milvus_path = os.getenv("milvus_path")
milvus_port = os.getenv("milvus_port")
milvus_db_name = os.getenv("milvus_db_name")
vector_index_type = os.getenv("vector_index_type")
vector_metric_type = os.getenv("vector_metric_type")


# Connect to milvus server (connector)
conn = connections.connect(
    alias="default",
    host=milvus_path,
    port=milvus_port,
    db_name=milvus_db_name
)

# 設定 Milvus collection 名稱
collection_name = 'trello_finder'

# 建立 collection
collection = Collection(collection_name)


## 搜尋 Top-K 相似文本
def search_vector(query_vector, limit=10, offset=0):
    try:
        # Start searching
        results = collection.search(
            data = [query_vector], 
            anns_field = "value", 
            param = {
                "index_type": vector_index_type,
                "metric_type": vector_metric_type, 
                "params": {"nprobe": 1},      
            },
            limit = limit, 
            offset = offset,
            expr = None,
            # set the names of the fields you want to retrieve from the search result.
            output_fields=['title', 'track_id'],
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