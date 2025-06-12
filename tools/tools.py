# tools.py

import os
import zipfile
import rarfile
from typing import List

def unzip_homework(zip_path: str, extract_to: str) -> str:
    """
    將指定的 ZIP 或 RAR 壓縮檔解壓縮到指定目錄。
    
    Args:
        zip_path: 壓縮檔的路徑。
        extract_to: 要解壓縮到的目標資料夾。
    
    Returns:
        一個表示操作結果的字串。
    """
    try:
        print(f"檢查檔案是否存在: {zip_path}")
        if not os.path.exists(zip_path):
            print(f"檔案不存在: {zip_path}")
            return f"錯誤：找不到壓縮檔 {zip_path}"
            
        print(f"檔案存在，大小: {os.path.getsize(zip_path)} 位元組")
        
        if not os.path.exists(extract_to):
            print(f"建立目標目錄: {extract_to}")
            os.makedirs(extract_to)
            
        if zip_path.endswith('.zip'):
            print("嘗試開啟 ZIP 檔案...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                print("成功開啟 ZIP 檔案，開始解壓縮...")
                # 獲取所有檔案列表
                file_list = zip_ref.namelist()
                print(f"壓縮檔中包含 {len(file_list)} 個檔案")
                
                # 逐個解壓縮檔案
                for file_name in file_list:
                    try:
                        # 處理檔案名稱中的特殊字元
                        safe_name = file_name.replace('/', os.path.sep).replace('\\', os.path.sep)
                        target_path = os.path.join(extract_to, safe_name)
                        
                        # 確保目標目錄存在
                        target_dir = os.path.dirname(target_path)
                        if not os.path.exists(target_dir):
                            os.makedirs(target_dir)
                            
                        # 解壓縮檔案
                        with zip_ref.open(file_name) as source, open(target_path, 'wb') as target:
                            target.write(source.read())
                            
                    except Exception as e:
                        print(f"解壓縮檔案 {file_name} 時發生錯誤: {e}")
                        continue
                        
                print("解壓縮完成")
        elif zip_path.endswith('.rar'):
            print("嘗試開啟 RAR 檔案...")
            with rarfile.RarFile(zip_path, 'r') as rar_ref:
                print("成功開啟 RAR 檔案，開始解壓縮...")
                rar_ref.extractall(extract_to)
                print("解壓縮完成")
        else:
            return f"錯誤：不支援的壓縮檔格式 {zip_path}"
            
        return f"成功將 {zip_path} 解壓縮到 {extract_to}"
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
        return f"錯誤：找不到壓縮檔 {zip_path}"
    except Exception as e:
        print(f"發生錯誤: {type(e).__name__}: {e}")
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