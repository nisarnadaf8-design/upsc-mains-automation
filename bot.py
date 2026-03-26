import os
import sys
import requests
from google import genai

print("--- STARTING BOT DIAGNOSTIC ---")

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

if not TELEGRAM_TOKEN or not CHAT_ID or not GEMINI_KEY:
    print("CRITICAL: One or more API keys are missing in GitHub Secrets!")
    sys.exit(1)

print("1. Keys loaded successfully.")
client = genai.Client(api_key=GEMINI_KEY)

mode = sys.argv[1] if len(sys.argv) > 1 else "questions"
print(f"2. Mode selected: {mode}")

if mode == "questions":
    prompt = "Write 3 simple UPSC questions. Plain text only. No markdown, no asterisks."
    
    try:
        print("3. Calling Gemini API...")
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        output = response.text
        print(f"4. Gemini Success! Generated {len(output)} characters.")
        
        with open('latest_questions.txt', 'w', encoding='utf-8') as f:
            f.write(output)
        
        print("5. Sending message to Telegram...")
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        # Notice: No parse_mode used at all to prevent formatting crashes
        payload = {"chat_id": CHAT_ID, "text": "TESTING QUESTIONS:\n\n" + output}
        
        tg_response = requests.post(url, json=payload)
        
        print(f"6. Telegram Status Code: {tg_response.status_code}")
        print(f"7. Telegram Response: {tg_response.text}")
        
        if tg_response.status_code != 200:
            print("CRITICAL: Telegram rejected the message!")
            sys.exit(1)  # This forces GitHub to show a Red 'X' Failed state
        else:
            print("8. SUCCESS: Message officially delivered to Telegram.")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

elif mode == "answers":
    print("Skipping answers mode for this diagnostic test.")
