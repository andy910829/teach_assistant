import ollama
from ollama import ChatResponse
from dotenv import load_dotenv
import os
import json
from typing import Dict, Any, Optional
from pprint import pprint

load_dotenv()

class AgentOllama:
    def __init__(self):
        # 初始化 Ollama 客戶端
        host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.client = ollama.Client(host=host, timeout =50)
        # 你的 Log 顯示是用 qwen3:32b，請確保環境變數 MODEL_NAME 設為此值
        self.model_name = os.getenv('OLLAMA_MODEL_NAME', 'qwen3:32b') 
        self.tools = None
        self.ollama_tools = None

    def set_tools(self, tools: list):
        """
        設置可用的工具列表
        參考 gemini.py 的邏輯，手動將 MCP 工具轉換為 Ollama (OpenAI compatible) 格式
        """
        self.ollama_tools = []
        for tool in tools:
            # 建立基本的函數定義結構
            function_def = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # 從 inputSchema 中獲取參數資訊 (與 gemini.py 邏輯一致)
            if hasattr(tool, 'inputSchema'):
                schema = tool.inputSchema
                if 'properties' in schema:
                    for param_name, param_info in schema['properties'].items():
                        function_def["parameters"]["properties"][param_name] = {
                            "type": param_info["type"],
                            "description": param_info.get("title", "") or param_info.get("description", "")
                        }
                if 'required' in schema:
                    function_def["parameters"]["required"] = schema['required']
            
            # Ollama 需要包裝在 "type": "function" 結構中
            self.ollama_tools.append({
                "type": "function",
                "function": function_def
            })

    def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成回應，處理 Ollama Object 回傳格式
        """
        messages = [{'role': 'user', 'content': prompt}]
        
        # 如果有上下文 (例如之前的對話歷史)，可以在這裡加入
        # if context: ...
        
        max_try = 3
        current_try = 0
        thinking = ""

        while current_try < max_try:
            try:
                # 發送請求到 Ollama
                response: ChatResponse = self.client.chat(
                    model=self.model_name,
                    messages=messages,
                    stream=False,
                    tools=self.ollama_tools if self.ollama_tools else None,
                    options={
                        "temperature": 0.1, # 降低溫度讓工具調用更精確
                        "num_ctx": 16384,    # 確保上下文長度足夠
                        "repeat_penalty": 1.2,
                    }
                )
                # pprint(response)
                # --- 針對你提供的格式進行解析 ---
                # response 是一個 ChatResponse 物件
                # response.message 是一個 Message 物件
                # with open("ollama_response_log.txt", "a", encoding="utf-8") as log_file:
                #     log_file.write(response, ensure_ascii=False, indent=2)
                #     log_file.write("\n\n====================\n\n")
                message = response.message
                
                content = message.thinking or ""
                tool_calls = getattr(message, 'tool_calls', []) # 這是 Object 的 list，不是 dict
                
                # 1. 檢查是否有原生的工具調用 (Tool Calls)
                if tool_calls:
                    formatted_tool_calls = []
                    for tc in tool_calls:
                        # tc.function 是一個物件，包含 name 和 arguments
                        formatted_tool_calls.append({
                            "tool": tc.function.name,
                            "parameters": tc.function.arguments # Ollama 庫通常會自動解析 JSON 參數為 dict
                        })
                    
                    return {
                        "response": content, # 可能會有思維過程或空字串
                        "tool_calls": formatted_tool_calls
                    }
                
                # 2. 如果沒有工具調用，嘗試解析內容是否為 JSON (為了相容某些 Prompt 寫法)
                # 你的 Log 顯示 content 是一大段 Markdown 文字，這通常會進入這裡並回傳純文字
                try:
                    # 嘗試解析 JSON (有些 Prompt 要求直接輸出 JSON 字串)
                    # 只有當內容看起來像 JSON 時才嘗試
                    if content.strip().startswith('{') and content.strip().endswith('}'):
                        result = json.loads(content)
                        return result
                except json.JSONDecodeError:
                    pass

                # 3. 回傳一般文字回應
                return {
                    "response": content,
                    "tool_calls": []
                }

            except Exception as e:
                print(f"================== OLLAMA Error (Try {current_try + 1}/{max_try}) ==================")
                print(f"Error type: {type(e)}")
                print(f"Error message: {str(e)}")
                # 如果是物件存取錯誤，印出 dir 來看屬性
                if 'response' in locals():
                    print(f"Response object dir: {dir(response)}")
                
                current_try += 1
                if current_try >= max_try:
                    return {
                        "response": f"Error calling Ollama: {str(e)}",
                        "tool_calls": []
                    }