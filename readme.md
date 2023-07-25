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
``` javascript
{
    "sentence" : "String",
}
```

**Response Value**
``` javascript
{
    "state" : "Boolean",
    "result" : "Array(768)",
}
```

### List top k similarity
**Request Value**
``` javascript
{
    "vector" : "Array(768)",
    "limit" : "Int",
}
```

**Response Value**
``` javascript
{
    "state" : "Boolean",
    "result" :  [
        {
            "id" : "String",
            "distance" : "Float",
            "preview" : "String",
            "track_id" : "String",
        } * "Limit"
    ] 
}
```

### List Article by Sentence
**Request Value**
``` javascript
{
    "sentence" : "String",
    "limit" : "Int",
    "anthropic_setup" : "Boolean", // 預設為 False, True 時會使用 Anthropic 回答問題
    "openai_setup" : "Boolean",  // 預設為 False, True 時會使用 ChatGPT 回答問題
}
```

**Response Value**
``` javascript
{
    "state" : "Boolean",
    "result" : [
        {
            "id" : "String",
            "distance" : "Float",
            "preview" : "String",
            "track_id" : "String",
            "answer_by_anthropic" : "String",
            "answer_by_openai" : "String",
        } * "Limit"
    ],
}
```

## Other Data:
Webhook id : **64be32eeb534868609690ed1**