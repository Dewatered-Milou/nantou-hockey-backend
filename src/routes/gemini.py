from flask import Blueprint, request, jsonify
import os
import json
import requests
from datetime import datetime

gemini_bp = Blueprint('gemini', __name__)

# Gemini API配置
GEMINI_API_KEY = "XXXX"  # 這裡會被用戶替換為真實的API key
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

def call_gemini_api(message):
    """
    調用真實的Gemini API
    """
    try:
        headers = {
            'Content-Type': 'application/json',
        }
        
        # 構建系統提示詞
        prompt_for_gemini = f"""
        你是一位專業、友善的「2025 南投國際曲棍球邀請賽」AI客服助手。
        請嚴格根據以下提供的「參考資料」來回答使用者的問題。
        不要編造任何參考資料中沒有的資訊。如果答案不在資料中，請禮貌地表示不清楚或引導使用者聯繫人工客服。
        請用繁體中文回答。

        ---
        [參考資料]
        {context}
        ---

        [使用者的問題]
        {message}
        """

        payload = {
            "contents": [{"parts": [{"text": prompt_for_gemini}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        # 如果API key是預設值，使用本地模擬回應
        if GEMINI_API_KEY == "XXXX":
            return get_local_response(message)
        
        # 調用真實的Gemini API
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                return {
                    'success': True,
                    'response': content,
                    'source': 'gemini_api'
                }
            else:
                return get_local_response(message)
        else:
            return get_local_response(message)
            
    except Exception as e:
        # 如果API調用失敗，使用本地回應
        return get_local_response(message)


def get_local_response(message):
    """
    本地模擬回應，當Gemini API不可用時使用
    """
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ['時間', '日期', '賽程']):
        return {
            'success': True,
            'response': '''📅 **2025南投國際男子曲棍球邀請賽**

🗓️ **賽事時間：** 2025年7月26日至31日（共6天）
⏰ **比賽時間：** 每日09:00-18:00
📍 **比賽地點：** 南投縣竹山高中曲棍球場

**賽程安排：**
• 7/26 (六)：開幕典禮 + 首輪比賽
• 7/27 (日)：小組賽第二輪
• 7/28 (一)：小組賽第三輪  
• 7/29 (二)：準決賽
• 7/30 (三)：季軍賽 + 冠軍賽
• 7/31 (四)：閉幕典禮 + 頒獎

需要了解特定場次的詳細時間嗎？''',
            'source': 'local'
        }
    
    elif any(keyword in message_lower for keyword in ['票', '購買', '價格']):
        return {
            'success': True,
            'response': '''🎫 **購票資訊**

**票種與價格：**
• **一般票：** NT$500
  - 所有比賽場次入場
  - 一般觀眾席座位
  - 賽事手冊

• **精緻票：** NT$1,200  
  - 精緻觀眾席座位
  - AR體驗APP
  - 精緻餐盒
  - 免費停車

• **VIP票：** NT$2,500
  - VIP專屬座位
  - 元宇宙觀賽體驗
  - 選手見面會
  - 專屬休息室

• **家庭套票：** NT$1,800
  - 4張一般票
  - 親子活動區
  - 家庭餐盒

**購票方式：** 官網線上購票或電洽049-123-4567''',
            'source': 'local'
        }
    
    else:
        return {
            'success': True,
            'response': '''👋 **歡迎來到南投國際曲棍球邀請賽！**

我是您的AI客服助手，可以協助您了解：

🎫 **購票資訊** - 票價、購票方式
📅 **賽程安排** - 比賽時間、場次
📍 **交通指引** - 比賽地點、交通方式  
🌟 **觀光套票** - 住宿、景點套票
🚀 **運動科技** - AI裁判、元宇宙觀賽
🏆 **隊伍報名** - 參賽資格、報名流程

請告訴我您想了解什麼資訊！

如需人工客服：**049-123-4567**''',
            'source': 'local'
        }

@gemini_bp.route('/chat', methods=['POST'])
def gemini_chat():
    """
    使用Gemini API的聊天端點
    """
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        context = data.get('context', '').strip() # 新增：接收 context

        if not message or not context:
            return jsonify({'error': '缺少 message 或 context'}), 400

        result = call_gemini_api(message, context) # 將 message 和 context 都傳進去
        return jsonify({
            'success': result['success'],
            'response': result['response'],
            'source': result['source'],
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'處理訊息失敗: {str(e)}'}), 500

@gemini_bp.route('/config', methods=['GET'])
def get_gemini_config():
    """
    獲取Gemini配置狀態
    """
    is_configured = GEMINI_API_KEY != "XXXX"
    
    return jsonify({
        'success': True,
        'configured': is_configured,
        'api_key_set': is_configured,
        'fallback_mode': not is_configured,
        'message': 'Gemini API已配置' if is_configured else 'Gemini API未配置，使用本地回應'
    }), 200

@gemini_bp.route('/config', methods=['POST'])
def update_gemini_config():
    """
    更新Gemini API配置（僅用於測試，實際部署時API key應在環境變數中設定）
    """
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({'error': 'API key不能為空'}), 400
        
        # 在實際部署中，這應該通過環境變數設定
        global GEMINI_API_KEY
        GEMINI_API_KEY = api_key
        
        return jsonify({
            'success': True,
            'message': 'Gemini API配置已更新',
            'configured': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'配置更新失敗: {str(e)}'}), 500

