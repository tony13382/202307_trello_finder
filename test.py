import os
from dotenv import load_dotenv
load_dotenv()
milvus_path = os.getenv("milvus_path")
milvus_port = os.getenv("milvus_port")
milvus_db_name = os.getenv("milvus_db_name")
vector_index_type = os.getenv("vector_index_type")
vector_metric_type = os.getenv("vector_metric_type")
print(milvus_path, vector_metric_type, vector_index_type, milvus_db_name, milvus_port)