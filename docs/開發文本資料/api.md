## API List
|  name | rount  | verb | description |
|  ---  | -----  | ---  | ----------- |
| Create embedding  | /api/vector | POST | 新增（轉換）一個向量 |
| List top k similarity | /api/vector | GET | 獲取相近的文本（by vector） |
| List Article by Sentence | /api/article | GET | 獲取相近的文本（by sentence） |
| Webhook for Trello | /api/webhook | POST | Trello Webhook 運作單元 |

## API Request & Response

### Create embedding
**Request Value**
``` javascript
{
    "sentence" : String,
}
```

**Response Value**
``` javascript
{
    "state" : Boolean,
    "result" : Array(768),
}
```

### List top k similarity
**Request Value**
``` javascript
{
    "vector" : Array(768),
    "limit" : Int,
}
```

**Response Value**
``` javascript
{
    "state" : Boolean,
    "result" :  [
        {
            "id" : String,
            "distance" : Float,
            "preview" : String,
            "track_id" : String,
        } * limit
    ] 
}
```

### List Article by Sentence
**Request Value**
``` javascript
{
    "sentence" : String,
    "limit" : Int, // 預設為 10, 可限制回傳數量
    "offset" : Int, // 預設為 0, 可選取回傳資料的起始位置
    "anthropic_setup" : Boolean, // 預設為 False, True 時會使用 Anthropic 回答問題
    "openai_setup" : Boolean,  // 預設為 False, True 時會使用 ChatGPT 回答問題
    "roBERTa_setup" : Boolean, // 預設為 False, True 時會使用 roBERTa 回答問題
    "bert_setup" : Boolean, // 預設為 False, True 時會使用 BERT 回答問題
}
```

**Response Value**
``` javascript
{
    "state" : Boolean,
    "result" : [
        {
            "id" : String,
            "distance" : Float,
            "preview" : String,
            "track_id" : String,
            "answer_by_anthropic" : String,
            "answer_by_openai" : String,
            "answer_by_RoBERTa" : String,
            "answer_by_BERT" : String,
        } * limit
    ],
}
```