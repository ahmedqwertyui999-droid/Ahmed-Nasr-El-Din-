import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# إعداد مفتاح ذكاء Gemini المجاني ومفاتيح فيسبوك
genai.configure(api_key="GEIMINI_API_KEY_المجاني")
PAGE_ACCESS_TOKEN = "مفتاح_صفحتك_من_فيسبوك"

# 1. استقبال الرسائل والتعليقات من فيسبوك
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # للتأكد من ربط السيرفر بفيسبوك لأول مرة
        verify_token = "كلمة_سر_تختارها_أنت"
        if request.args.get("hub.verify_token") == verify_token:
            return request.args.get("hub.challenge")
        return "خطأ في التحقق", 403
        
    elif request.method == 'POST':
        data = request.get_json()
        
        # إذا كانت رسالة مسنجر خاصة
        if data.get('object') == 'page':
            for entry in data['entry']:
                for messaging_event in entry.get('messaging', []):
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        user_text = messaging_event['message']['text']
                        
                        # نرسل الكلام لـ Gemini يجهز الرد
                        bot_reply = ask_gemini(user_text)
                        send_messenger_message(sender_id, bot_reply)
                        
                # إذا كان تعليق على منشور
                for change in entry.get('changes', []):
                    if change.get('field') == 'feed' and change['value'].get('item') == 'comment':
                        comment_id = change['value']['comment_id']
                        comment_text = change['value']['message']
                        
                        # نخليه يرد على التعليق بذكاء
                        bot_reply = ask_gemini(comment_text)
                        reply_to_comment(comment_id, bot_reply)
                        
        return "تم الاستلام", 200

# 2. وظيفة إرسال الكلام لذكاء Gemini المجاني
def ask_gemini(prompt):
    model = genai.GenerativeModel('gemini-pro')
    # هنا تديه أوامر وتعرفه بنفسه
    full_prompt = f"أنت خبير علم نفس ومساعد لصفحتنا، رد على هذا المتابع باختصار ولطف: {prompt}"
    response = model.generate_content(full_prompt)
    return response.text

# 3. وظيفة إرسال الرد للمسنجر
def send_messenger_message(recipient_id, text):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    requests.post(url, json=payload)

# 4. وظيفة الرد على التعليق
def reply_to_comment(comment_id, text):
    url = f"https://graph.facebook.com/v19.0/{comment_id}/comments?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"message": text}
    requests.post(url, json=payload)

# 5. وظيفة النشر التلقائي (تشتغل بجدولة زمنية)
@app.route('/auto-post', methods=['POST'])
def auto_post():
    # نخلي الذكاء الاصطناعي يكتب بوست جديد عن علم النفس براهو
    post_content = ask_gemini("اكتب منشوراً مشوقاً ومفيداً عن علم النفس وعلاقات الناس لفيسبوك")
    
    url = f"https://graph.facebook.com/v19.0/me/feed?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"message": post_content}
    response = requests.post(url, json=payload)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(port=5000)
