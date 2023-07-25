# Trello Finder
## API List
|  name | rount  | verb | description |
|  ---  | -----  | ---  | ----------- |
| Create embedding  | /api/vector | POST | 新增（轉換）一個向量 |
| List top k similarity | /api/vector | GET | 獲取相近的文本（by vector） |
| List Article by Sentence | /api/article | GET | 獲取相近的文本（by sentence） |

## API Request & Response

### Create embedding
**Request Value**
| name | type |
| ---- | ---- |
| sentence | String |

**Response Value**
| name | type |
| ---- | ---- |
| state | Boolean |
| result | Array(768) |

### List top k similarity
**Request Value**
| name | type |
| ---- | ---- |
| vector | Array(768) |
| limit | Int |

**Response Value**
| name | type |
| ---- | ---- |
| state | Boolean |
| result | Array(limit) |

item in result list
``` json
{
    "id" : String,
    "distance" : Float,
    "preview" : String,
    "track_id" : String,
}
```

### List Article by Sentence
**Request Value**
| name | type |
| ---- | ---- |
| sentence | String |
| limit | Int |
| anthropic_setup | Boolean (預設為 False, True 時會使用 GPT 回答問題) |
| openai_setup | Boolean (預設為 False, True 時會使用 GPT 回答問題)  |

**Response Value**
| name | type |
| ---- | ---- |
| state | Boolean |
| result | Array(limit) |

item in result list
``` json
{
    "id" : String,
    "distance" : Float,
    "preview" : String,
    "track_id" : String,
    "answer_by_anthropic" : String,
    "answer_by_openai" : String,
}
```

## Other Data:
Webhook id : **64be32eeb534868609690ed1**