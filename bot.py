import os
import sys
import requests
import time
from google import genai

# Load API keys
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Initialize the Gemini Client
client = genai.Client(api_key=GEMINI_KEY)

def send_telegram_message(text):
    """Sends message to Telegram and forces plain text if formatting fails."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    
    for chunk in chunks:
        payload = {"chat_id": CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            print(f"Telegram Markdown rejected. Sending plain text... Error: {response.text}")
            safe_payload = {"chat_id": CHAT_ID, "text": chunk}
            requests.post(url, json=safe_payload)

def generate_with_retry(prompt):
    """Fetches AI response using the active 2026 free-tier model."""
    model_name = "gemini-2.5-flash"
    
    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text
    except Exception as e:
        print(f"API Error: {e}")
        print("Retrying in 15 seconds...")
        time.sleep(15)
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "questions"
    
    if mode == "questions":
        prompt = "Provide 3 analytical UPSC GS-1 Society questions and 3 GS-4 Ethics questions. Output only the questions, numbered clearly."
        
        try:
            output_text = generate_with_retry(prompt)
            
            with open('latest_questions.txt', 'w', encoding='utf-8') as f:
                f.write(output_text)
            
            message = "🌅 **Good Morning! Today's Practice Questions:**\n\n" + output_text
            send_telegram_message(message)
            print("Successfully sent questions to Telegram!")
            
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            sys.exit(1) # This ensures GitHub shows a RED 'X' if it fails!
            
    elif mode == "answers":
        try:
            with open('latest_questions.txt', 'r', encoding='utf-8') as f:
                questions = f.read()
                
            prompt = f"Provide highly structured UPSC-standard answers for these questions. For each, give 3 distinct intro options, 3 forward-looking conclusion options, and a concise body. Question list:\n{questions}"
            
            output_text = generate_with_retry(prompt)
            message = "📚 **Afternoon Answer Key:**\n\n" + output_text
            send_telegram_message(message)
            print("Successfully sent answers to Telegram!")
            
        except FileNotFoundError:
            msg = "⚠️ No questions found for today. The morning schedule needs to run successfully first."
            send_telegram_message(msg)
            print(msg)
            sys.exit(1)
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
