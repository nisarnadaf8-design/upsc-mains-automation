import os
import sys
import requests
import time
from google import genai

# Load environment variables
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Initialize the new Gemini client
client = genai.Client(api_key=GEMINI_KEY)

def send_telegram_message(text):
    """Sends a message to Telegram, splitting it if it exceeds character limits."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            payload = {"chat_id": CHAT_ID, "text": text[i:i+4000], "parse_mode": "Markdown"}
            requests.post(url, json=payload)
    else:
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, json=payload)

def generate_with_retry(prompt):
    """Fetches the AI response using the most stable free-tier model."""
    model_name = "gemini-1.5-flash" 
    
    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text
    except Exception as e:
        print(f"First attempt hit a speedbump: {e}")
        print("Waiting 35 seconds to clear Google's rate limits...")
        time.sleep(35)
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "questions"
    
    if mode == "questions":
        prompt = "Provide 3 high-quality UPSC GS-1 Society questions and 3 GS-4 Ethics questions. Ensure they are analytical and syllabus-aligned. Output only the questions, numbered clearly."
        try:
            output_text = generate_with_retry(prompt)
            
            with open('latest_questions.txt', 'w') as f:
                f.write(output_text)
            
            message = "🌅 **Good Morning! Today's Practice Questions:**\n\n" + output_text
            send_telegram_message(message)
        except Exception as e:
            print(f"Critical Error generating questions: {e}")
            
    elif mode == "answers":
        try:
            with open('latest_questions.txt', 'r') as f:
                questions = f.read()
            prompt = f"Provide highly structured UPSC-standard answers for these questions. For each, give 3 distinct intro options, 3 forward-looking conclusion options, and a concise body. Question list:\n{questions}"
            
            output_text = generate_with_retry(prompt)
            send_telegram_message("📚 **Afternoon Answer Key:**\n\n" + output_text)
            
        except FileNotFoundError:
            send_telegram_message("⚠️ No questions found for today. The morning schedule needs to run successfully first.")
        except Exception as e:
            print(f"Critical Error generating answers: {e}")

if __name__ == "__main__":
    main()
