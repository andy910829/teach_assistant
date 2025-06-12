# tools.py

import os
import zipfile
from typing import List

def unzip_homework(zip_path: str, extract_to: str) -> str:
    """
    將指定的 ZIP 壓縮檔解壓縮到指定目錄。
    
    Args:
        zip_path: 壓縮檔的路徑。
        extract_to: 要解壓縮到的目標資料夾。
    
    Returns:
        一個表示操作結果的字串。
    """
    try:
        if not os.path.exists(extract_to):
            os.makedirs(extract_to)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return f"成功將 {zip_path} 解壓縮到 {extract_to}"
    except FileNotFoundError:
        return f"錯誤：找不到壓縮檔 {zip_path}"
    except Exception as e:
        return f"解壓縮時發生錯誤: {e}"

def read_student_code(student_folder_path: str) -> str:
    """
    讀取指定學生資料夾中所有 .c 和 .h 檔案的內容，並合併成一個字串。
    
    Args:
        student_folder_path: 學生作業的資料夾路徑。
        
    Returns:
        包含所有程式碼內容的單一字串，或是一條錯誤訊息。
    """
    code_contents = []
    try:
        for filename in os.listdir(student_folder_path):
            if filename.endswith(('.c', '.h')):
                file_path = os.path.join(student_folder_path, filename)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code_contents.append(f"--- 檔案: {filename} ---\n\n{f.read()}\n\n")
        
        if not code_contents:
            return "錯誤：在此資料夾中找不到任何 .c 或 .h 檔案。"
            
        return "".join(code_contents)
    except FileNotFoundError:
        return f"錯誤：找不到資料夾 {student_folder_path}"
    except Exception as e:
        return f"讀取檔案時發生錯誤: {e}"


def write_grading_report(folder_path: str, student_id: str, student_name: str, score: int, comments: str) -> str:
    """
    在學生的資料夾內寫入一份包含評分結果的報告檔案 (report.txt)。
    
    Args:
        folder_path: 學生作業的資料夾路徑。
        student_id: 學生學號。
        student_name: 學生姓名。
        score: 分數 (0-100)。
        comments: 評語。
        
    Returns:
        一個表示操作結果的字串。
    """
    report_content = (
        f"學號: {student_id}\n"
        f"姓名: {student_name}\n"
        f"分數: {score}\n\n"
        f"評語:\n"
        f"----------------------------------------\n"
        f"{comments}\n"
        f"----------------------------------------\n"
    )
    report_path = os.path.join(folder_path, "grading_report.txt")
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        return f"評分報告已成功寫入 {report_path}"
    except Exception as e:
        return f"寫入報告時發生錯誤: {e}"