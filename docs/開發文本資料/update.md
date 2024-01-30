# V3
**ChangeLog:**
- 文字雲格式更改
- 擴展模糊與精準搜尋
- TF 模塊正式入庫
<br><br>
![Trello 系統流程設計圖v3.0.png](Trello%20系統流程設計圖v3.0-WorkFlow.png)
![Trello 系統流程設計圖v3.0.png](Trello%20系統流程設計圖v3.0-ER%20Model.png)
`08/12`

# V2.2
**ChangeLog:**
- 修改閥值 distance < 2.5（非相似文章會剔除）
- 最高回覆提升至 20 筆
- 新增回覆過濾機制（**只有包含以下任一條件才會回覆**）<br><br>
    ```
    - 小幫手我想問
    - 小幫手請問
    - 我想問
    - 請問
    - 是什麼
    - 什麼是
    - 問號：？ / ?
    ``` 
    <br>
![Trello 系統流程設計圖v2.2.png](Trello%20系統流程設計圖v2.2.png)
`08/07`

# V2.1
**ChangeLog:**
- 新增閥值 distance < 2（非相似文章會剔除）
- 新增 10 in 1 文字雲
- 排序倒轉 (現在 rank 1-10 越上面越接近)
- 增加關鍵字推薦功能 (文本模糊注入)

![Trello 系統流程設計圖v2.0.png](Trello%20系統流程設計圖v2.0.png)
`08/04`

# V1.0
**ChangeLog:**
- 基礎功能實作

![Trello 系統流程設計圖v1.0.png](Trello%20系統流程設計圖v1.0.png)
`07/26`