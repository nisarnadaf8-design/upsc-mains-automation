import os
import sys
import requests
import google.generativeai as genai

# Load environment variables
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "questions"
    
    if mode == "questions":
        prompt = "Generate 3 UPSC Mains standard questions on Indian Society (GS1) and 3 on Ethics (GS4). Only output the questions, nicely formatted."
        response = model.generate_content(prompt)
        message = "🌅 **Good Morning! Here are your Mains Questions for today:**\n\n" + response.text
        
        # Save questions to a file so we can answer the exact same ones later
        with open('today_questions.txt', 'w') as f:
            f.write(response.text)
            
    elif mode == "answers":
        # Read the morning's questions
        try:
            with open('today_questions.txt', 'r') as f:
                questions = f.read()
            prompt = f"Provide detailed, structured UPSC-standard answers for the following questions:\n{questions}"
            response = model.generate_content(prompt)
            message = "📚 **Afternoon! Here are the detailed answers:**\n\n" + response.text
        except FileNotFoundError:
            message = "Error: Could not find today's questions to answer."

    send_telegram_message(message)

if __name__ == "__main__":
    main()
