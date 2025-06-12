# main.py
from pprint import pprint
import os
# import google.generativeai as genai
from dotenv import load_dotenv
import json
import asyncio
from model.gemini import AgentGemini
# 從我們自己寫的檔案中匯入工具
from mcp_client import MCPToolClient

# 載入環境變數 (API Key)
load_dotenv()
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
prompt_dir = 'prompt/'

# --- 1. 定義評分標準 (這是給 Gemini 的核心指令) ---

with open(f'{prompt_dir}system_prompt.txt', 'r', encoding='utf-8') as f:
    GRADING_RUBRIC = f.read()

async def grade_single_student(student_folder_path: str, model: AgentGemini, mcp_client: MCPToolClient) -> None:
    """評分單一學生的作業"""
    # try:
        # 檢查資料夾命名格式
    folder_name = os.path.basename(student_folder_path)
    if "_" not in folder_name:
        error_msg = f"資料夾命名格式錯誤：{folder_name}，應為「學號_姓名」格式"
        await mcp_client.call_tool("write_grading_report", {
            "student_id": "unknown",
            "student_name": "unknown",
            "score": 0,
            "comments": error_msg,
            "output_path": os.path.join(student_folder_path, "grading_report.txt")
        })
        return

    student_id, student_name = folder_name.split("_", 1)
    
    # 讀取學生的程式碼
    c_files = []
    h_files = []
    
    for file in os.listdir(student_folder_path):
        if file.endswith('.c'):
            with open(os.path.join(student_folder_path, file), 'r', encoding='utf-8') as f:
                c_files.append(f.read())
        elif file.endswith('.h'):
            with open(os.path.join(student_folder_path, file), 'r', encoding='utf-8') as f:
                h_files.append(f.read())
    
    if not c_files and not h_files:
        error_msg = "找不到 .c 或 .h 檔案"
        await mcp_client.call_tool("write_grading_report", {
            "student_id": student_id,
            "student_name": student_name,
            "score": 0,
            "comments": error_msg,
            "output_path": os.path.join(student_folder_path, "grading_report.txt")
        })
        return
    
    # 組合提示
    prompt = f"""請評分以下學生的作業：

學號：{student_id}
姓名：{student_name}

程式碼：
"""
    if c_files:
        prompt += "\nC 檔案：\n" + "\n---\n".join(c_files)
    if h_files:
        prompt += "\n\n標頭檔：\n" + "\n---\n".join(h_files)
        
    prompt += f"""

評分標準：
{GRADING_RUBRIC}

請根據評分標準評分，並使用 write_grading_report 工具生成評分報告。
評分報告應包含：
1. 分數（0-100）
2. 詳細評語
3. 改進建議

請確保評分報告的輸出路徑為：{os.path.join(student_folder_path, "grading_report.txt")}
"""
    with open("prompt.txt", 'w', encoding='utf-8') as f:
        f.write(prompt)
    # 生成評分
    response = model.generate_text(prompt)
    # 處理工具調用
    if "tool_calls" in response:
        for tool_call in response["tool_calls"]:
            if tool_call["tool"] == "write_grading_report":
                await mcp_client.call_tool("write_grading_report", tool_call["parameters"])
        
    # except Exception as e:
    #     print(f"評分過程發生錯誤：{str(e)}")
    #     # 寫入錯誤報告
    #     await mcp_client.call_tool("write_grading_report", {
    #         "student_id": student_id if 'student_id' in locals() else "unknown",
    #         "student_name": student_name if 'student_name' in locals() else "unknown",
    #         "score": 0,
    #         "comments": f"評分過程發生錯誤：{str(e)}",
    #         "output_path": os.path.join(student_folder_path, "grading_report.txt")
    #     })

async def main():
    """主執行函數"""
    # 使用絕對路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    homework_zip_file = os.path.join(current_dir, "hw100034936.zip")
    unzip_target_dir = os.path.join(current_dir, "assignments", "graded_homework")

    print("--- C語言助教 Agent ---")
    print(f"正在處理壓縮檔：{homework_zip_file}")
    print(f"解壓縮目標目錄：{unzip_target_dir}")
    
    # 確保目標目錄存在
    os.makedirs(unzip_target_dir, exist_ok=True)
    
    # 初始化 MCP 客戶端和 Gemini 模型
    mcp_client = MCPToolClient("tools/mcp_tools.py")
    model = AgentGemini()
    
    # 獲取可用工具列表
    tools = await mcp_client.list_available_tools()
    model.set_tools(tools)
    
    # 初始動作：解壓縮作業
    result = await mcp_client.call_tool("unzip_folder", {
        "source_path": homework_zip_file,
        "target_path": unzip_target_dir
    })
    print(result)
    
    if "錯誤" in result:
        return # 如果解壓縮失敗，就直接結束

    # 獲取解壓縮後的目錄
    main_homework_folder = unzip_target_dir

    if not os.path.isdir(main_homework_folder):
        print(f"[錯誤] 解壓縮目錄不存在: {main_homework_folder}")
        return

    # 遍歷所有學生資料夾
    for student_dir_name in os.listdir(main_homework_folder):
        student_folder_path = os.path.join(main_homework_folder, student_dir_name)
        
        # 如果是目錄，直接處理
        if os.path.isdir(student_folder_path):
            await grade_single_student(student_folder_path, model, mcp_client)
        # 如果是壓縮檔，先解壓縮再處理
        elif student_dir_name.endswith(('.zip', '.rar')):
            nested_zip_path = student_folder_path
            nested_extract_dir = os.path.splitext(student_folder_path)[0]
            nested_result = await mcp_client.call_tool("unzip_folder", {
                "source_path": nested_zip_path,
                "target_path": nested_extract_dir
            })
            if "成功" in nested_result:
                await grade_single_student(nested_extract_dir, model, mcp_client)
            else:
                print(f"[錯誤] 無法解壓縮學生作業: {student_dir_name}")
                print(nested_result)
            
    print("\n--- 所有作業已評分完畢 ---")

if __name__ == "__main__":
    asyncio.run(main())