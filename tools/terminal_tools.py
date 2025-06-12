import pexpect

# 啟動一個 bash shell 進程
child = pexpect.spawn('/bin/bash', encoding='utf-8')

# 等待 shell 的命令提示符出現 (使用正則表達式)
child.expect(r'\$ ') 

# 打印出 shell 啟動時的歡迎訊息
print("Shell ready. Initial output:")
print(child.before) 

# 發送 'ls -l' 命令
child.sendline('ls -l')

# 再次等待命令提示符，這意味著 'ls' 命令已經執行完畢
child.expect(r'\$ ')

# child.before 現在包含了 'ls -l' 命令的完整輸出
ls_output = child.before
print("\n--- Output of 'ls -l' ---")
print(ls_output)

# Agent 可以分析 ls_output，然後決定下一步...
child.sendline('echo "Hello Agent"')
child.expect(r'\$ ')
echo_output = child.before
print("\n--- Output of 'echo' ---")
print(echo_output)

# 結束 session
child.close()