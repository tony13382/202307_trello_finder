# Trello 知識小幫手 2.0
![Cover of plan](./static/cover/cover.png)
<br><br>清華大學 學習科學與科技研究所 區國良教授研究室計劃案 **（Trello 知識小幫手 2.0）** <br>開發者：清華大學 學習科學與科技研究所 **呂亮進**


---
### 系統啟用步驟
1. 申請 Trello API Key
2. 取得 Trello API Password
3. 確認 `MongoDB (Local)`、`Milvus (Docker)`、`RabbitMQ (Docker)` 服務啟用
4. 確認 `RabbitMQ (Docker)` 服務啟用
5. 執行 `rmq_service.py` 啟動 RabbitMQ 服務<br><br>
   >多服務則使用多個終端機同時打開即可<br>每新增一個就代表同時能多服務一位
   ``` python
    python rmq_service.py
   ```
   <br>
6. 執行 `app.py` 啟動 API Server<br><br>
   ``` python
    python app.py
   ```
   <br>
7. Trello Webhook Feedback URL 已上線於 `localhost:5000/webhook3`
8. 設定 Trello Webhook (可透過 IP 位址或 ngrok 進行測試)
   

---
### 運用中不可處置資料
| 文檔名稱 | 用途 | 備註 |
| :--- | :--- | :--- |
| [jf-openhuninn-2.0.ttf](./static/others/jf-openhuninn-2.0.ttf) |  文字雲採用字體  | 開源授權。[來源](https://justfont.com/huninn/) |
| [stopwords_chinese.txt](./setting/stopwords_chinese.txt) | 斷詞停用字列表 | （基於 [baipengyan/Chinese-StopWords](https://github.com/baipengyan/Chinese-StopWords/blob/master/ChineseStopWords.txt) 停用表翻譯＋擴充） |
| [MONPA 斷詞字典資料夾](./setting/monpa_dict/) | 斷詞權重調整 | 斷詞權重調整（根據 [斷詞編撰](./docs/斷詞編撰/) 編制 [教育部關鍵字](./setting/monpa_dict/keyword_by_edugov.txt)），如需自定請使用 [自定義擴充關鍵字](./setting/monpa_dict/customize.txt) |
| [action_word_list.txt](./setting/action_word_list.txt) | Trello 啟動詞設定 | - |
| [not_found_msg_list.txt](./setting/not_found_msg_list.txt) | 無資料罐頭訊息設定 | 查無結果隨機抽取 |
| [Post.ipynb- colab](https://colab.research.google.com/drive/1LX8n4HB-GEFX9aWn60nsdrU9yUvvqNmd?usp=drive_link) | 部署用筆記本文件 | 須申請權限 |
| [Trello Helper 部署清單](https://docs.google.com/spreadsheets/d/1aijNun9tFA1iyUcvc5q8sN-xQnVlfSumsZDI_oDR_Kg/edit?usp=drive_link) | 部署清單，包含 board id, webhook id | 須申請權限 |

### 備用資料
| 文檔名稱 | 用途 | 備註 |
| :--- | :--- | :--- |
| [0926_new.xlsx](./docs/文章原始資料/0926_new.xlsx) |  原始文章資料 | 於 2023/07/20 交接 |
| [Pansci.csv](./docs/文章原始資料/Pansci.csv)、[Scitechvista.csv](./docs/文章原始資料/Scitechvista.csv) |  原始文章資料 | 於 2023/10/23 交接 |
| [20240131-AllArticle.xlsx](./docs/文章原始資料/20240131-AllArticle.xlsx) |  原始文章資料 | 於 2024/01/31 交接 |
| [V1 切割 Excel 列表](./docs/文章原始資料/20240206_V1切割/Excel/) |  重構文章資料（原本V1） | 於 2024/02/06 交接 |

> ⚠｜部分資料不上載

### 技術文件
| 文檔名稱 | 用途 | 備註 |
| :--- | :--- | :--- |
| [Trello 小幫手 2.0*](https://www.canva.com/design/DAFpubaReH0/Yxxx9ETMI7shWic20NYheA/view) |  技術簡介 | Trello 小幫手 2.0 說明與介紹 |
| [API 技術文件](./docs/開發文本資料/api.md) |  API 文件 | API 規範與使用 |
| [testservice.ipynb](./testservice.ipynb) |  測試文件 | 功能模塊測試 |
| [Trello 系統流程設計圖.drawio](./docs/開發文本資料/Trello%20系統流程設計圖.drawio) |  開發技術文件 | - |
| [Trello 系統流程設計圖 更新紀錄](./docs/開發文本資料/update.md) |  開發文件 | - |

---

![System WorkFlow](./docs/開發文本資料/Trello%20系統流程設計圖v3.0-WorkFlow.png)

---

![System ER Model](./docs/開發文本資料/Trello%20系統流程設計圖v3.0-ER%20Model.png)

---

### 參考文件
| 文檔名稱 | 用途 | 備註 |
| :--- | :--- | :--- |
| [The Trello REST API*](https://developer.atlassian.com/cloud/trello/rest/api-group-cards/#api-cards-id-put) | 第三方技術文件 | Trello API 說明與介紹 |
| [Get Started Building on Trello*](https://developer.atlassian.com/cloud/trello/) | 第三方技術文件 | POWER-UPS 說明與介紹、Webhook API 設定 |
| [Flask Documentation*](https://flask.palletsprojects.com/en/2.3.x/quickstart/) | 第三方技術文件 | Flask (API Server) 技術說明與介紹 |
| [Milvus documentation*](https://milvus.io/docs) | 第三方技術文件 | Milvus (向量資料庫) 技術說明與介紹 |
| [SentenceTransformers Documentation*](https://www.sbert.net/index.html) | 第三方技術文件 | SBERT（文本向量化） 技術說明與介紹 |
| [罔拍 MONPA GitHub*](https://github.com/monpa-team/monpa) | 第三方技術文件 | MONPA（斷詞模組） 說明與介紹 |
| [正體中文斷詞系統應用於大型語料庫之多方評估研究*](https://aclanthology.org/2022.rocling-1.24.pdf) | 論文 | 斷詞模組相關論文（作為選擇依據） |
| [shigureni free illust*](https://www.shigureni.com/) | 圖庫 | 開發中使用的圖庫（可商用） |



