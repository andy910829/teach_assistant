
# C 語言 AI 助教 (C Language AI TA)

這是一個使用 Python 和 Google Gemini API 開發的自動化 C 語言程式作業批改工具。本專案模擬一位助教，能夠自動解壓縮學生繳交的作業、讀取程式碼、根據預設的評分標準進行靜態分析，並生成詳細的評分報告。

## 核心功能

- **自動解壓縮**：支援 `.zip`, `.rar`, `.7z` 等多種壓縮檔格式，能自動處理學生繳交的壓縮檔。
- **AI 靜態分析**：利用 Gemini 大型語言模型分析 C 語言程式碼的可讀性、結構、邏輯和是否符合作業要求。
- **自訂評分標準**：助教的評分邏輯與作業要求完全定義在 `prompt/system_prompt.txt` 中，方便根據不同作業需求進行客製化。
- **生成評分報告**：為每位學生生成一份獨立的 `grading_report.txt`，包含分數、評語和改進建議。
- **工具化設計**：專案封裝了 `unzip_folder` 和 `write_grading_report` 等工具，供 AI 模型彈性調用，提高了處理複雜情況（如巢狀壓縮檔）的能力。

## 環境設定

1.  **複製專案**：
    ```bash
    git clone https://github.com/andy910829/teach_assistant.git
    cd teach_assistant
    ```

2.  **安裝 Python**：
    請確保您已安裝 Python 3.9 或更高版本。

3.  **安裝相依套件**：
    ```bash
    pip install -r requirements.txt
    ```

4.  **設定 API 金鑰**：
    - 在專案根目錄下建立一個名為 `.env` 的檔案。
    - 在 `.env` 檔案中加入您的 Google Gemini API 金鑰：
      ```
      GEMINI_API_KEY="YOUR_API_KEY_HERE"
      ```

## 使用方法

1.  **放置作業檔案**：
    將要批改的學生作業壓縮檔（例如 `hw100038106.zip`）放置在專案的根目錄下。

2.  **修改主程式**：
    打開 `main.py` 檔案，修改 `homework_zip_file` 變數，使其指向您要處理的作業壓縮檔。

3.  **執行批改**：
    執行主程式，AI 助教將開始自動化批改流程。
    ```bash
    python main.py
    ```

4.  **查看報告**：
    批改完成後，程式會將解壓縮後的學生作業存放在 `assignments/graded_homework/` 目錄下。每位學生的資料夾內都會有一份 `grading_report.txt` 評分報告。

## 專案結構

```
. C語言助教
├── assignments/
│   └── graded_homework/      # 存放已解壓縮和批改的學生作業
├── model/
│   └── gemini.py             # Gemini 模型的封裝
├── prompt/
│   └── system_prompt.txt     # AI 助教的核心指令與評分標準
├── tools/
│   ├── mcp_tools.py          # 定義可供 AI 調用的工具 (unzip, write_report)
│   └── ...
├── .env                      # (需手動建立) 存放 API 金鑰
├── .gitignore
├── main.py                   # 專案主執行檔
├── requirements.txt          # Python 相依套件列表
└── README.md                 # 專案說明文件
```

## 如何客製化

本專案最大的彈性在於評分標準的客製化。若要修改作業要求或評分細節，只需編輯 `prompt/system_prompt.txt` 檔案即可。AI 助教的行為將完全根據該檔案的內容來調整，無需修改任何 Python 程式碼。
