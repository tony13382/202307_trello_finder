# Trello 知識小幫手 2.0
![Cover of plan](./static/cover/cover.png)
清華大學 學習科學與科技研究所 區國良老師研究室計劃案 **（Trello 知識小幫手 2.0）** <br>開發者：清華大學 學習科學與科技研究所 **呂亮進**

---
### 運用中不可處置資料
| 文檔名稱 | 用途 | 備註 |
| :--- | :--- | :--- |
| [doc_converter.ipynb](./docs/doc_converter.ipynb) | 資料轉換 | 文字雲、mongo milvus 資料庫轉存 |
| [jf-openhuninn-2.0.ttf](./docs/jf-openhuninn-2.0.ttf) |  相依於 [process_words.py](./toolbox/process_words.py) 、 [doc_converter.ipynb](./docs/doc_converter.ipynb) | 文字雲採用字體，[來源](https://justfont.com/huninn/) |
| [stopwords_chinese.txt](./docs/stopwords_chinese.txt) | 相依於 [process_words.py](./toolbox/process_words.py) 、 [doc_converter.ipynb](./docs/doc_converter.ipynb) | 斷詞停用字列表<br>（基於 [goto456/stopwords](https://github.com/goto456/stopwords) 哈工大停用词表擴充） |
| [MONPA_斷詞字典.txt](./docs/MONPA_斷詞字典.txt) | 相依於 [process_words.py](./toolbox/process_words.py) | 斷詞權重調整 |
| [vector_all.json](./docs/vector_all.json) |  df 備份檔案、相依於 [doc_converter.ipynb](./docs/doc_converter.ipynb) | 包含所有文本向量化的 dataframe |

### 備用資料
| 文檔名稱 | 用途 | 備註 |
| :--- | :--- | :--- |
| [0926_new.xlsx](./docs/文章原始資料/0926_new.xlsx) |  原始文章資料 | 學姊於 07/20 交接 |
| [static / images / *.png](./static/images) | 文字雲圖片備份 | 對應 `原始資料 df.index` |
| [tony13382/trello_helper_img・Github*](https://github.com/tony13382/trello_helper_img) | 圖床 | 用於文章文字雲展示 |

### 技術文件
| 文檔名稱 | 用途 | 備註 |
| :--- | :--- | :--- |
| [Trello 小幫手 2.0*](https://www.canva.com/design/DAFpubaReH0/BbDmz605ypPRGSZAJdPh8g/edit) |  技術簡介 | Trello 小幫手 2.0 說明與介紹 |
| [API 技術文件](./docs/開發文本資料/api.md) |  API 文件 | API 規範與使用 |
| [testservice.ipynb](./testservice.ipynb) |  測試文件 | 功能模塊測試 |
| [Trello 系統流程設計圖.drawio](./docs/開發文本資料/Trello%20系統流程設計圖.drawio) |  開發技術文件 | - |
| [Trello 系統流程設計圖 更新紀錄](./docs/開發文本資料/update.md) |  開發文件 | - |

---

![System WorkFlow](./docs/開發文本資料/Trello%20系統流程設計圖v2.2.png)

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

---

### Other Data:
Webhook id : `64be32eeb534868609690ed1`