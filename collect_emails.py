#!/usr/bin/env python3
"""
简单的邮箱收集脚本
用于收集对AI-Agent-Hub感兴趣的用户邮箱
当用户提交意向时，记录到本地文件
"""

import os
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# 数据存储文件
DATA_FILE = "collected_emails.json"

class EmailHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求，返回简单的统计信息"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # 读取数据
            emails = self.load_emails()
            total = len(emails)
            today_emails = [e for e in emails if e.get('date', '').startswith(datetime.now().strftime('%Y-%m-%d'))]
            today_count = len(today_emails)
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>AI-Agent-Hub 邮箱收集后台</title></head>
            <body>
                <h1>AI-Agent-Hub 意向用户统计</h1>
                <p><strong>总意向用户：</strong> {total} 人</p>
                <p><strong>今日新增：</strong> {today_count} 人</p>
                <p><strong>最后更新：</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h2>最近10条记录：</h2>
                <table border="1" cellpadding="5">
                <tr><th>邮箱</th><th>提交时间</th><th>IP地址</th></tr>
            """
            
            # 显示最近10条记录
            for email in emails[-10:]:
                html += f"""
                <tr>
                    <td>{email.get('email', 'N/A')}</td>
                    <td>{email.get('date', 'N/A')}</td>
                    <td>{email.get('ip', 'N/A')}</td>
                </tr>
                """
            
            html += """
                </table>
                
                <h2>原始数据（JSON）：</h2>
                <pre style="background: #f0f0f0; padding: 10px;">
            """ + json.dumps(emails, ensure_ascii=False, indent=2) + """
                </pre>
                
                <p><a href="/download">下载数据文件</a></p>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/download':
            # 提供数据文件下载
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Disposition', 'attachment; filename="emails.json"')
            self.end_headers()
            
            with open(DATA_FILE, 'rb') as f:
                self.wfile.write(f.read())
                
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """处理POST请求，收集邮箱"""
        if self.path == '/collect':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # 解析表单数据
            parsed_data = urllib.parse.parse_qs(post_data)
            email = parsed_data.get('email', [''])[0]
            
            if email and '@' in email:
                # 收集信息
                email_data = {
                    'email': email,
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'ip': self.client_address[0],
                    'user_agent': self.headers.get('User-Agent', 'Unknown')
                }
                
                # 保存到文件
                emails = self.load_emails()
                emails.append(email_data)
                self.save_emails(emails)
                
                print(f"[{datetime.now()}] 收集到邮箱: {email} 来自IP: {self.client_address[0]}")
                
                # 返回成功响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'success', 'message': '邮箱已记录'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                # 返回错误响应
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'error', 'message': '无效的邮箱地址'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def load_emails(self):
        """从文件加载邮箱数据"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_emails(self, emails):
        """保存邮箱数据到文件"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(emails, f, ensure_ascii=False, indent=2)

def start_server(port=8080):
    """启动HTTP服务器"""
    server = HTTPServer(('0.0.0.0', port), EmailHandler)
    print(f"邮箱收集服务器启动，监听端口 {port}")
    print(f"管理界面: http://localhost:{port}")
    print(f"API端点: http://localhost:{port}/collect")
    print("按 Ctrl+C 停止服务器")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器停止")
        server.server_close()

if __name__ == '__main__':
    # 如果数据文件不存在，创建空文件
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    start_server(8080)