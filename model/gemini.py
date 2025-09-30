import google.generativeai as genai
from google.generativeai import types
from dotenv import load_dotenv
import os
import json
from typing import Dict, Any, Optional
from pprint import pprint

load_dotenv()

class AgentGemini:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel(os.getenv('MODEL_NAME'))
        self.tools = None
        self.gemini_tools = None

    def set_tools(self, tools: list):
        """設置可用的工具列表"""
        self.tools = tools
        
        # 將 MCP 工具轉換為 Gemini 函數宣告格式
        function_declarations = []
        for tool in tools:
            function_declaration = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # 從 inputSchema 中獲取參數資訊
            if hasattr(tool, 'inputSchema'):
                schema = tool.inputSchema
                if 'properties' in schema:
                    for param_name, param_info in schema['properties'].items():
                        function_declaration["parameters"]["properties"][param_name] = {
                            "type": param_info["type"],
                            "description": param_info.get("title", "")
                        }
                if 'required' in schema:
                    function_declaration["parameters"]["required"] = schema['required']
                
            function_declarations.append(function_declaration)
            
        # 創建 Gemini 工具配置
        self.gemini_tools = types.Tool(function_declarations=function_declarations)
        self.config = types.GenerationConfig()

    def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成回應，可能包含工具調用
        
        Args:
            prompt: 提示文字
            context: 額外的上下文資訊
            
        Returns:
            包含回應和工具調用的字典
        """
        # 發送請求
        response = self.model.generate_content(
            contents=prompt,
            generation_config=self.config,
            tools=[self.gemini_tools] if self.gemini_tools else None
        )
        
        # 檢查是否有函數調用
        # print("================== GEMINI response ==================")
        # print(response.candidates[0])
        # print(response)

        max_try = 3
        current_try = 0

        while current_try < max_try:
            try:
                function_call = None
                text_response = None
                    
                candidate = response.candidates[0]
                # 安全地檢查 parts
                parts = getattr(candidate.content, 'parts', [])   
                # 檢查所有 parts 中的 function_call
                for part in parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_call = part.function_call
                    if hasattr(part, 'text') and part.text:
                        text_response = part.text
                        
                if function_call:
                    return {
                        "response": text_response if text_response is not None else function_call.name,
                        "tool_calls": [{
                            "tool": function_call.name,
                            "parameters": function_call.args
                        }]
                    }
                elif candidate.finish_reason == 10:
                    current_try += 1
                    if current_try >= max_try:
                        return {
                            "response": "重試次數已達上限",
                            "error": "MALFORMED_FUNCTION_CALL"
                        }
                    print(f"遇到 MALFORMED_FUNCTION_CALL，正在進行第 {current_try} 次重試...")
                    continue
                else:
                    # 如果不是函數調用，嘗試解析 JSON 回應
                    try:
                        result = json.loads(response.text)
                        return result
                    except json.JSONDecodeError:
                        # 如果不是 JSON 格式，返回純文字回應
                        return {
                            "response": response.text,
                            "tool_calls": []
                        }      
            except Exception as e:
                print("================== GEMINI response ==================")
                print(response.candidates[0].finish_reason)
                print(response)     
                current_try += 1       