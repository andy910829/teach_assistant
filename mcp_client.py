# mcp_client.py  
import asyncio  
from mcp import ClientSession, StdioServerParameters  
from mcp.client.stdio import stdio_client  

class MCPToolClient:  
    def __init__(self, server_script_path: str):  
        self.server_params = StdioServerParameters(  
            command="python",  
            args=[server_script_path],  
            env=None,  
        )  
        self.chat_history = 'chat_history.txt' 
      
    async def call_tool(self, tool_name: str, arguments: dict):  
        """调用MCP工具"""  
        async with stdio_client(self.server_params) as (read, write):  
            async with ClientSession(read, write) as session:  
                # 初始化连接  
                await session.initialize()  
                  
                # 调用工具  
                result = await session.call_tool(tool_name, arguments)  
                with open(self.chat_history, 'a', encoding='utf-8') as f:  
                    f.write(f"\n工具調用結果:\n{result}\n")
                return result  
      
    async def list_available_tools(self):  
        """获取可用工具列表"""  
        async with stdio_client(self.server_params) as (read, write):  
            async with ClientSession(read, write) as session:  
                await session.initialize()  
                tools = await session.list_tools()  
                return tools.tools