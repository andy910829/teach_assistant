from mcp.server.fastmcp import FastMCP
import os
import zipfile
import rarfile
import shutil
import logging

# 設定 rarfile 的 unrar 工具路徑
rarfile.UNRAR_TOOL = "C:\\Program Files\\WinRAR\\UnRAR.exe"

# 創建 FastMCP 實例
mcp = FastMCP("Teaching Assistant")

@mcp.tool()
def unzip_folder(source_path: str, target_path: str) -> str:
    """解壓縮資料夾，支援 ZIP 和 RAR 格式"""
    try:
        # 檢查來源檔案是否存在
        if not os.path.exists(source_path):
            return f"錯誤：找不到來源檔案 {source_path}"
        
        # 確保目標目錄存在
        os.makedirs(target_path, exist_ok=True)
        
        # 根據副檔名選擇解壓縮方法
        if source_path.lower().endswith('.zip'):
            with zipfile.ZipFile(source_path, 'r') as zip_ref:
                # 處理每個檔案
                for file_info in zip_ref.infolist():
                    try:
                        # 解壓縮單一檔案
                        zip_ref.extract(file_info, target_path)
                    except Exception as e:
                        logging.warning(f"解壓縮檔案 {file_info.filename} 時發生錯誤：{str(e)}")
                        continue
                        
        elif source_path.lower().endswith('.rar'):
            with rarfile.RarFile(source_path, 'r') as rar_ref:
                # 處理每個檔案
                for file_info in rar_ref.infolist():
                    try:
                        # 解壓縮單一檔案
                        rar_ref.extract(file_info, target_path)
                    except Exception as e:
                        logging.warning(f"解壓縮檔案 {file_info.filename} 時發生錯誤：{str(e)}")
                        continue
        else:
            return f"錯誤：不支援的檔案格式 {os.path.splitext(source_path)[1]}"
        
        return f"成功解壓縮 {source_path} 到 {target_path}"
        
    except Exception as e:
        return f"解壓縮過程發生錯誤：{str(e)}"

@mcp.tool()
def write_grading_report(student_id: str, student_name: str, score: int, comments: str, output_path: str) -> str:
    """寫入評分報告到指定路徑"""
    try:
        # 確保輸出目錄存在
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # 格式化評分報告內容
        report_content = f"""評分報告
==========

學號：{student_id}
姓名：{student_name}
分數：{score}

評語：
{comments}
"""
        
        # 寫入檔案
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return f"成功寫入評分報告到 {output_path}"
        
    except Exception as e:
        return f"寫入評分報告時發生錯誤：{str(e)}"


# def register_tools():
#     """註冊所有工具"""
#     return mcp 

if __name__ == "__main__":
    mcp.run(transport="stdio")