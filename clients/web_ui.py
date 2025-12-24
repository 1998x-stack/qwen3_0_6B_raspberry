#!/usr/bin/env python3
"""
web_ui.py - Qwen3 简易 Web 界面
提供一个简单的网页聊天界面，与 llama.cpp server 通信

安装依赖:
    pip install flask requests

运行:
    python3 web_ui.py

访问:
    http://raspberrypi.local:5000
"""

from flask import Flask, render_template_string, request, jsonify
import requests
import json

app = Flask(__name__)

# llama.cpp server 配置
LLAMA_SERVER_URL = "http://localhost:8080/v1/chat/completions"

# HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qwen3 Chat - 树莓派</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            width: 90%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .header p {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            animation: fadeIn 0.3s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .message.assistant .message-content {
            background: white;
            color: #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .message.system .message-content {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeeba;
            text-align: center;
            max-width: 100%;
        }
        
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
        }
        
        #userInput {
            flex: 1;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        #userInput:focus {
            border-color: #667eea;
        }
        
        #sendBtn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        
        #sendBtn:hover:not(:disabled) {
            transform: scale(1.05);
        }
        
        #sendBtn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 10px;
            color: #666;
        }
        
        .loading.active {
            display: block;
        }
        
        .loading::after {
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        
        .stats {
            padding: 10px 20px;
            background: #f8f9fa;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #666;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Qwen3 Chat</h1>
            <p>在树莓派上运行的 AI 助手</p>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message system">
                <div class="message-content">
                    👋 你好！我是 Qwen3，一个运行在树莓派上的 AI 助手。问我任何问题吧！
                </div>
            </div>
        </div>
        
        <div class="loading" id="loading">AI 正在思考</div>
        
        <div class="input-container">
            <input 
                type="text" 
                id="userInput" 
                placeholder="输入你的问题..."
                autocomplete="off"
            >
            <button id="sendBtn">发送</button>
        </div>
        
        <div class="stats" id="stats">
            准备就绪
        </div>
    </div>

    <script>
        const chatContainer = document.getElementById('chatContainer');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        const loading = document.getElementById('loading');
        const stats = document.getElementById('stats');
        
        let isGenerating = false;
        
        // 添加消息到聊天界面
        function addMessage(role, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            messageDiv.appendChild(contentDiv);
            chatContainer.appendChild(messageDiv);
            
            // 滚动到底部
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // 发送消息
        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message || isGenerating) return;
            
            // 添加用户消息
            addMessage('user', message);
            userInput.value = '';
            
            // 显示加载状态
            isGenerating = true;
            sendBtn.disabled = true;
            loading.classList.add('active');
            stats.textContent = '正在生成回复...';
            
            const startTime = Date.now();
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    addMessage('system', '❌ 错误: ' + data.error);
                } else {
                    addMessage('assistant', data.response);
                    
                    // 更新统计信息
                    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
                    stats.textContent = `响应时间: ${duration}s | Tokens: ${data.tokens || 'N/A'}`;
                }
            } catch (error) {
                addMessage('system', '❌ 网络错误: ' + error.message);
                stats.textContent = '请求失败';
            } finally {
                isGenerating = false;
                sendBtn.disabled = false;
                loading.classList.remove('active');
            }
        }
        
        // 事件监听
        sendBtn.addEventListener('click', sendMessage);
        
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // 自动聚焦输入框
        userInput.focus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 发送到 llama.cpp server
        payload = {
            'messages': [
                {'role': 'user', 'content': user_message}
            ],
            'temperature': 0.7,
            'max_tokens': 256,
            'stream': False
        }
        
        response = requests.post(
            LLAMA_SERVER_URL,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': f'服务器错误: {response.status_code}'
            }), 500
        
        result = response.json()
        
        # 提取回复
        assistant_message = result['choices'][0]['message']['content']
        
        # 提取 token 信息
        usage = result.get('usage', {})
        total_tokens = usage.get('total_tokens', 0)
        
        return jsonify({
            'response': assistant_message,
            'tokens': total_tokens
        })
        
    except requests.exceptions.Timeout:
        return jsonify({'error': '请求超时，请稍后重试'}), 504
    
    except requests.exceptions.ConnectionError:
        return jsonify({
            'error': '无法连接到 llama.cpp server，请确保服务已启动'
        }), 503
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """健康检查"""
    try:
        response = requests.get(f"http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            return jsonify({'status': 'ok', 'llama_server': 'running'})
        else:
            return jsonify({'status': 'degraded', 'llama_server': 'error'}), 503
    except:
        return jsonify({'status': 'error', 'llama_server': 'offline'}), 503

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Qwen3 Web UI 启动中...")
    print("=" * 80)
    print()
    print("访问地址:")
    print("  本地: http://localhost:5000")
    print("  局域网: http://<树莓派IP>:5000")
    print()
    print("确保 llama.cpp server 已在端口 8080 运行")
    print("按 Ctrl+C 退出")
    print("=" * 80)
    print()
    
    app.run(
        host='0.0.0.0',  # 监听所有网络接口
        port=5000,
        debug=False
    )