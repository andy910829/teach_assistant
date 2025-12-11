# main.py
from pprint import pprint
import argparse
import os
# import google.generativeai as genai
from dotenv import load_dotenv
import asyncio
from model.gemini import AgentGemini
from model.ollamaAPI import AgentOllama
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
        return error_msg

    student_id, student_name = folder_name.split("_", 1)
    
    # 讀取學生的程式碼
    c_files = []
    h_files = []
    zip_files = []
    py_files = []
    cpp_files = []
    makefile_files = []
    other_files = []
    file_structure = []
    try:
        if "grading_report.txt" not in os.listdir(student_folder_path):
            for root, dirs, files in os.walk(student_folder_path):
                # 計算相對路徑
                rel_path = os.path.relpath(root, student_folder_path)
                if rel_path == '.':
                    rel_path = ''
                    
                # 添加資料夾資訊
                for dir_name in dirs:
                    file_structure.append(f"📁 {os.path.join(rel_path, dir_name)}/")
                    
                # 添加檔案資訊
                for file_name in files:
                    if file_name.endswith('.zip') or file_name.endswith('.rar') or file_name.endswith('.tar') or file_name.endswith('.7z'):
                        zip_files.append(file_name)
                    file_path = os.path.join(rel_path, file_name)
                    file_structure.append(f"📄 {file_path}")
                    
                    # 讀取檔案內容
                    full_path = os.path.join(root, file_name)
                    try:
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except UnicodeDecodeError as e:
                            print(f"UTF-8 解碼失敗 {e}")
                            with open(full_path, 'r') as f:
                                content = f.read()
                        except Exception as e:
                            print(f"讀取檔案失敗 {e}")
                        if file_name.endswith('.c'):
                            c_files.append(content)
                        elif file_name.endswith('.h'):
                            h_files.append(content)
                        elif file_name.endswith('.cpp'):
                            cpp_files.append(content)
                        elif file_name.endswith('.py'):
                            py_files.append(content)
                        elif file_name.endswith('makefile') or file_name.endswith('Makefile'):
                            makefile_files.append(f"檔案：{file_path}\n內容：\n{content}\n")
                        else:
                            other_files.append(f"檔案：{file_path}\n內容：\n{content}\n")
                    except UnicodeDecodeError:
                        # 如果檔案不是文字格式，只記錄檔案名稱
                        other_files.append(f"檔案：{file_path} (二進位檔案)")
                    except Exception as e:
                        other_files.append(f"檔案：{file_path} (無法讀取：{str(e)})")
            if not c_files and not h_files and not cpp_files and not py_files and not zip_files:
                error_msg = "找不到 .c, .cpp, .h, .py 檔案或壓縮檔"
                return error_msg
            # if not c_files and not h_files:
            #     error_msg = "找不到 .c 或 .h 檔案"
            #     await mcp_client.call_tool("write_grading_report", {
            #         "student_id": student_id,
            #         "student_name": student_name,
            #         "score": 0,
            #         "comments": error_msg,
            #         "output_path": os.path.join(student_folder_path, "grading_report.txt")
            #     })
            #     return
            
            # 組合提示
            prompt = f"""請評分以下學生的作業：

            學號：{student_id}
            姓名：{student_name}

            檔案結構:
            {chr(10).join(file_structure)}

            程式碼：
            """    
            if not c_files and not h_files and not cpp_files and not py_files:
                prompt += f"無程式碼提供，請根據檔案結構判斷是否需要解壓縮，解壓縮檔案路徑為:{os.path.join(student_folder_path)}，將上述路徑加上要解壓縮的資料夾檔名才是完整的解壓縮路徑，請將該路徑設置為source_path。並且將該檔案的解壓縮目標設置為{os.path.join(student_folder_path)}加上解壓縮後你希望該資料夾命名的名稱，才是完整的target_path"
            else:
                if c_files:
                    prompt += "\nC 檔案：\n" + "\n---\n".join(c_files)
                if cpp_files:
                    prompt += "\nCPP 檔案：\n" + "\n---\n".join(cpp_files)
                if h_files:
                    prompt += "\n\n標頭檔：\n" + "\n---\n".join(h_files)
                if py_files:
                    prompt += "\n\nPython 檔案：\n" + "\n".join(py_files)
                if makefile_files:
                    prompt += "\n\nMakefile 檔案：\n" + "\n---\n".join(makefile_files)
            prompt += f"""

            評分標準：
            {GRADING_RUBRIC}

            請根據評分標準評分，並使用 write_grading_report 工具生成評分報告。
            評分報告應包含：
            1. 分數（70-100）
            2. 詳細評語
            3. 改進建議

            請確保評分報告的輸出路徑為：{os.path.join(student_folder_path, "grading_report.txt")}
            """
            print(f"{student_folder_path}作業批改中....")
            with open("prompt.txt", 'w', encoding='utf-8') as f:
                f.write(prompt)
            # 生成評分
            response = model.generate_text(prompt)
            # 處理工具調用
            if "tool_calls" in response:
                for tool_call in response["tool_calls"]:
                    if tool_call["tool"] == "write_grading_report":
                        await mcp_client.call_tool("write_grading_report", tool_call["parameters"])
                        return 'STOP' 
                    if tool_call["tool"] == "unzip_folder":
                        await mcp_client.call_tool("unzip_folder", tool_call['parameters'])
                        return 'KEEP'
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
        else:
            return 'STOP'  # 已經有評分報告，跳過
    except Exception as e:
        print(f"處理學生作業時發生錯誤：{str(e)}")
        return 'STOP'    

async def main(args):
    """主執行函數"""
    # 使用絕對路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    homework_zip_file = os.path.join(current_dir, args.zip)
    unzip_target_dir = os.path.join(current_dir, "assignments", "graded_homework")

    print("--- C/C++/python語言助教 Agent ---")
    print(f"正在處理壓縮檔：{homework_zip_file}")
    print(f"解壓縮目標目錄：{unzip_target_dir}")
    
    # 確保目標目錄存在
    os.makedirs(unzip_target_dir, exist_ok=True)
    
    # 初始化 MCP 客戶端和 Gemini 模型
    mcp_client = MCPToolClient("tools/mcp_tools.py")
    if args.model == 'ollama':
        model = AgentOllama()
    else:
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

    if len(os.listdir(main_homework_folder))<=1:
        while len(os.listdir(main_homework_folder))<=1:
            main_homework_folder = os.path.join(main_homework_folder, os.listdir(main_homework_folder)[0])
        print(main_homework_folder)

    # 遍歷所有學生資料夾
    for student_dir_name in os.listdir(main_homework_folder):
        student_folder_path = os.path.join(main_homework_folder, student_dir_name)
        # 如果是目錄，直接處理
        if os.path.isdir(student_folder_path):
            result = await grade_single_student(student_folder_path, model, mcp_client)
            if result == 'STOP':
                print(f"{student_folder_path}作業批改完畢。")
                continue
            elif result != 'KEEP':
                print(f"[錯誤] 無法處理學生作業: {student_dir_name} {result}")
                continue
            while True:
                result = await grade_single_student(student_folder_path, model, mcp_client)
                if result == 'STOP':
                    print(f"{student_folder_path}作業批改完畢。")
                    break
        # 如果是壓縮檔，先解壓縮再處理
        elif student_dir_name.endswith(('.zip', '.rar')):
            nested_zip_path = student_folder_path
            nested_extract_dir = os.path.splitext(student_folder_path)[0]
            nested_result = await mcp_client.call_tool("unzip_folder", {
                "source_path": nested_zip_path,
                "target_path": nested_extract_dir
            })
            if "成功" in nested_result:
                result = await grade_single_student(nested_extract_dir, model, mcp_client)
            else:
                print(f"[錯誤] 無法解壓縮學生作業: {student_dir_name}")
                print(nested_result)
            
    print("\n--- 所有作業已評分完畢 ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C語言助教 (Gemini/Ollama)")
    parser.add_argument(
        "-z", "--zip", 
        default="",
        help="輸入的作業壓縮檔路徑 (預設: hw100039477.zip)"
    )
    parser.add_argument(
        "-m", "--model", 
        choices=['gemini', 'ollama'], 
        default="gemini",
        help="選擇使用的 AI 模型 (預設: gemini)"
    )
    args = parser.parse_args()
    asyncio.run(main(args))