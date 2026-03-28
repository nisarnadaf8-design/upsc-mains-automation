import os
import sys
import json
import requests
import time
from datetime import datetime, timezone, timedelta
from google import genai
 
# ── API Keys ──────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID        = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_KEY     = os.environ.get('GEMINI_API_KEY')
 
client = genai.Client(api_key=GEMINI_KEY)
 
# ── Model Fallback Chain ──────────────────────────────────────────────────────
MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-1.5-flash-001",
]
 
# ── Topic Rotation with PYQ Themes ───────────────────────────────────────────
# Each entry has: topic + core PYQ themes from that topic (2013-2024)
 
GS1_TOPICS = [
    {
        "topic": "Indian Society: Diversity, Social Stratification and Caste",
        "pyq_themes": [
            "Caste as a social institution vs political tool",
            "Sanskritisation and Westernisation — Srinivas",
            "Social mobility and barriers in Indian society",
            "Role of reservations in addressing historical injustice",
            "Intersection of caste, class and gender",
        ]
    },
    {
        "topic": "Role of Women: Empowerment, Violence and Representation",
        "pyq_themes": [
            "Feminisation of poverty and its causes",
            "Self Help Groups as instruments of women empowerment",
            "Political representation of women — 33% reservation debate",
            "Domestic violence and legal safeguards",
            "Gender gap in workforce participation — LFPR data",
        ]
    },
    {
        "topic": "Communalism, Regionalism and Secularism",
        "pyq_themes": [
            "Constitutional secularism vs Western secularism",
            "Communalism as a political mobilisation tool",
            "Regionalism — threat or opportunity for national integration",
            "Role of media in amplifying communal tensions",
            "Composite culture and syncretic traditions of India",
        ]
    },
    {
        "topic": "Population: Demographic Dividend, Ageing and Migration",
        "pyq_themes": [
            "Demographic dividend — conditions and risks",
            "Ageing population and social security challenges",
            "Rural to urban migration and its consequences",
            "Population policy — beyond fertility control",
            "Brain drain vs brain gain debate",
        ]
    },
    {
        "topic": "Poverty, Social Exclusion and Inclusive Growth",
        "pyq_themes": [
            "Multidimensional poverty — beyond income measures",
            "Social exclusion of tribal communities",
            "Role of MGNREGA in rural poverty alleviation",
            "Inclusive growth vs trickle-down economics",
            "Linkage between poverty and lack of education",
        ]
    },
    {
        "topic": "Urbanisation: Smart Cities, Slums and Governance",
        "pyq_themes": [
            "Slum formation as a governance failure",
            "Smart Cities Mission — promise vs ground reality",
            "Urban local bodies and 74th Constitutional Amendment",
            "Push and pull factors of rural-urban migration",
            "Challenges of urban waste management",
        ]
    },
    {
        "topic": "Globalisation and Its Impact on Indian Society",
        "pyq_themes": [
            "Cultural homogenisation vs cultural diversity",
            "Globalisation and widening inequality",
            "Impact on Indian family structure — nuclear families",
            "Gig economy and changing nature of work",
            "Globalisation and women — empowerment or exploitation",
        ]
    },
]
 
GS4_TOPICS = [
    {
        "topic": "Ethics and Human Interface: Determinants of Ethical Behaviour",
        "pyq_themes": [
            "Role of family, society and educational institutions in value formation",
            "Influence of religion on ethical behaviour",
            "Conscience as a moral guide vs social norms",
            "Moral relativism vs universal ethics",
            "Ethics of care — Gilligan's framework",
        ]
    },
    {
        "topic": "Attitude: Formation, Change and Social Influence",
        "pyq_themes": [
            "Cognitive dissonance and attitude change",
            "Role of attitude in administrative decision-making",
            "Prejudice and stereotyping in bureaucracy",
            "Social influence on individual moral choices",
            "Moral courage to challenge wrong attitudes",
        ]
    },
    {
        "topic": "Civil Services Values: Integrity, Impartiality and Empathy",
        "pyq_themes": [
            "Integrity beyond legal compliance — spirit of the law",
            "Impartiality when political pressure conflicts with duty",
            "Empathy in public service delivery",
            "Dedication to public service vs personal career",
            "Objectivity in evidence-based policy making",
        ]
    },
    {
        "topic": "Emotional Intelligence in Governance",
        "pyq_themes": [
            "Self-awareness and self-regulation in crisis management",
            "Empathy as a tool for inclusive administration",
            "Emotional intelligence vs IQ in leadership",
            "Managing stress and burnout in civil services",
            "EI in conflict resolution and team building",
        ]
    },
    {
        "topic": "Moral Thinkers: Gandhi, Ambedkar, Aristotle and Kant",
        "pyq_themes": [
            "Gandhian ethics — trusteeship and non-violence in governance",
            "Ambedkar — constitutional morality vs social morality",
            "Kant's categorical imperative in public administration",
            "Aristotle's virtue ethics — character of a civil servant",
            "Relevance of ancient Indian ethics — Kautilya's Arthashastra",
        ]
    },
    {
        "topic": "Probity in Governance: Transparency and Accountability",
        "pyq_themes": [
            "RTI Act as a tool of accountability",
            "Whistleblower protection — ethics of dissent",
            "Conflict of interest in public office",
            "Ethical dilemmas of loyalty vs public interest",
            "Citizen's charter and service delivery ethics",
        ]
    },
    {
        "topic": "Case Studies: Ethical Dilemmas in Administration",
        "pyq_themes": [
            "Conflict between orders from superior and public welfare",
            "Corruption — to report or not — dilemma of a junior officer",
            "Disaster management — allocation of limited resources ethically",
            "Political interference in transfer and posting",
            "Ethical handling of confidential government information",
        ]
    },
]
 
def today_topics():
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    day = ist.timetuple().tm_yday
    gs1 = GS1_TOPICS[day % len(GS1_TOPICS)]
    gs4 = GS4_TOPICS[day % len(GS4_TOPICS)]
    return gs1, gs4, ist.strftime("%d %b %Y")
 
# ── Telegram ──────────────────────────────────────────────────────────────────
def send_message(text: str):
    url    = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        payload = {"chat_id": CHAT_ID, "text": chunk}
        try:
            r = requests.post(url, json=payload, timeout=15)
            if not r.ok:
                print(f"Telegram error {r.status_code}: {r.text}")
            else:
                print("Chunk sent OK.")
        except Exception as e:
            print(f"Telegram exception: {e}")
        time.sleep(1)
 
def send_error(context: str, err: Exception):
    msg = f"BOT ERROR [{context}]\n{type(err).__name__}: {err}"
    print(msg)
    send_message(msg)
 
# ── Gemini with Fallback ──────────────────────────────────────────────────────
def generate(prompt: str) -> str:
    for model in MODELS:
        for attempt in range(2):
            try:
                resp = client.models.generate_content(model=model, contents=prompt)
                print(f"Success with model: {model}")
                return resp.text
            except Exception as e:
                if "429" in str(e):
                    print(f"{model} quota exhausted, switching to next model...")
                    break   # skip remaining attempts, try next model
                print(f"{model} attempt {attempt+1} failed: {e}")
                if attempt == 0:
                    time.sleep(15)
    raise RuntimeError("All models exhausted. Check your Gemini API quota.")
 
# ── Prompts ───────────────────────────────────────────────────────────────────
 
QUESTION_PROMPT = """You are a senior UPSC Mains question paper setter with 20 years experience.
 
TODAY'S TOPICS AND PYQ THEMES:
GS-1 (Society): {gs1_topic}
Key PYQ Themes: {gs1_themes}
 
GS-4 (Ethics): {gs4_topic}
Key PYQ Themes: {gs4_themes}
 
YOUR TASK:
Generate exactly 4 fresh questions inspired by the PYQ themes above.
Do NOT copy previous year questions directly. Frame NEW questions on the SAME themes.
 
OUTPUT FORMAT (plain text only, no asterisks, no symbols):
 
========================================
GS-1 SOCIETY: {gs1_topic}
========================================
 
Q1. (10 Marks | 150 words)
[Frame a crisp 2-sentence analytical question.
Must test conceptual understanding.
Draw from PYQ themes but use fresh wording.
Example style: "Examine the... Discuss its implications on..."]
 
Q2. (15 Marks | 200 words)
[Frame a question requiring multi-dimensional analysis.
Should cover at least 2 angles — social, economic, political or gender.
Example style: "Critically analyse... How has... affected...?"]
 
========================================
GS-4 ETHICS: {gs4_topic}
========================================
 
Q3. (10 Marks | 150 words)
[Frame a conceptual ethics question.
Must relate to civil services context.
Example style: "What do you understand by... How does it influence...?"]
 
Q4. (20 Marks | Case Study)
[Write a realistic 4-5 line scenario:
A civil servant faces a dilemma involving conflict between duty, political pressure,
public welfare and personal values.
Make it specific — include location, department, situation details.
End with: "What should the officer do? Examine the ethical issues involved
and suggest a course of action with justification."]
 
STRICT RULES:
- Questions must be short — maximum 3 sentences each
- No sub-parts like a), b), c)
- Plain text only — no asterisks, no bold, no symbols
- Questions must be analytical, not factual recall
"""
 
ANSWER_PROMPT = """You are a UPSC Mains topper and an expert answer writer.
Write model answers for ALL 4 questions below.
 
ANSWER STRUCTURE (follow this for every answer):
 
---
Q[number]. [Question topic] | [Marks] | [Word limit]
 
INTRODUCTION:
[2-3 lines. Use ONE of these styles:
- Powerful quote by a thinker, leader or Supreme Court judgment
- Shocking data or fact that frames the problem
- Constitutional provision or SDG goal linkage
- Futuristic or aspirational opening
Never start with "In India..." or "Since ancient times..."]
 
BODY:
[Use numbered headings. Under each heading:
- 1 heading line in CAPITALS
- 2 crisp lines of explanation using UPSC keywords
- 1 Indian example: scheme / Supreme Court case / committee / state initiative / data post-2019]
 
[Number of headings by marks:
- 10 marks: 3 headings
- 15 marks: 5 headings
- 20 marks case study: 6 headings]
 
WAY FORWARD: (include only where reform or policy suggestions are relevant)
- 3-4 crisp bullet points
- Each point must be specific, not generic
- Link to committees, NEP, SDG, Vision India 2047 where possible
 
CONCLUSION:
[1-2 lines. Use ONE of these styles:
- SDG goal linkage
- Vision India 2047 / Amrit Kaal reference
- Futuristic statement
- Relevant quote
Never repeat the introduction.]
 
---
 
WORD LIMITS (strictly follow):
- 10-mark answer: 150 words
- 15-mark answer: 200 words
- 20-mark case study: 250 words
 
DIMENSIONS TO COVER (pick relevant ones per question):
GS-1: Social / Economic / Political / Gender / Legal / Regional / Global comparison / Data
GS-4: Individual ethics / Institutional ethics / Constitutional morality /
       Philosophical backing / Emotional intelligence / Governance angle /
       Stakeholder impact / Way forward for systemic reform
 
UPSC KEYWORDS TO USE NATURALLY:
GS-1: social capital, demographic dividend, feminisation of poverty, social mobility,
      constitutional morality, majoritarianism, composite culture, social stratification,
      SDG-1/5/10, inclusive growth, intersectionality
GS-4: moral courage, conflict of interest, probity, public trust, value pluralism,
      whistleblower, consequentialism, deontological ethics, empathy,
      emotional intelligence, constitutional ethics, Nolan principles
 
DATA SOURCES TO CITE:
NFHS-5 (2021), NCRB 2023, Economic Survey 2024, Census 2011,
World Bank Report, UNDP HDI 2024, MoSPI, SECC, ILO Report,
Supreme Court judgments, CAG reports
 
LANGUAGE RULES:
- Simple and direct English
- Every sentence must add value — no filler phrases
- Plain text only — no asterisks, no hashtags, no markdown symbols
- Each Indian example must be specific (name the scheme, case, state or year)
 
QUESTIONS TO ANSWER:
{questions}
"""
 
# ── Files ─────────────────────────────────────────────────────────────────────
QUESTIONS_FILE = "latest_questions.txt"
META_FILE      = "latest_meta.json"
 
# ── Morning: Send Questions ───────────────────────────────────────────────────
def run_questions():
    gs1, gs4, date_str = today_topics()
 
    print(f"GS1: {gs1['topic']} | GS4: {gs4['topic']}")
 
    prompt = QUESTION_PROMPT.format(
        gs1_topic  = gs1["topic"],
        gs1_themes = "\n- ".join(gs1["pyq_themes"]),
        gs4_topic  = gs4["topic"],
        gs4_themes = "\n- ".join(gs4["pyq_themes"]),
    )
 
    questions = generate(prompt)
 
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        f.write(questions)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "gs1": gs1["topic"],
            "gs4": gs4["topic"],
            "date": date_str
        }, f)
 
    header = (
        f"UPSC MAINS DAILY PRACTICE\n"
        f"Date: {date_str}\n"
        f"========================================\n"
        f"GS-1 Topic : {gs1['topic']}\n"
        f"GS-4 Topic : {gs4['topic']}\n"
        f"========================================\n\n"
        f"Write your answers before 1:00 PM IST.\n"
        f"Model answer key drops at 1:00 PM.\n\n"
        f"TODAY'S QUESTIONS:\n\n"
    )
 
    send_message(header + questions)
    print("Questions sent successfully.")
 
# ── Afternoon: Send Answers ───────────────────────────────────────────────────
def run_answers():
    if not os.path.exists(QUESTIONS_FILE):
        send_message(
            "UPSC Bot Alert:\n"
            "Answer key could not be sent today.\n"
            "Reason: Morning questions file not found.\n"
            "Check if the 8 AM job ran and committed latest_questions.txt."
        )
        print("Questions file missing.")
        return
 
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = f.read()
 
    meta = {}
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
 
    print(f"Generating answers for: {meta}")
 
    prompt  = ANSWER_PROMPT.format(questions=questions)
    answers = generate(prompt)
 
    header = (
        f"UPSC MAINS MODEL ANSWER KEY\n"
        f"Date: {meta.get('date', 'Today')}\n"
        f"========================================\n"
        f"GS-1 : {meta.get('gs1', '')}\n"
        f"GS-4 : {meta.get('gs4', '')}\n"
        f"========================================\n\n"
        f"Compare your answers. Focus on dimensions you missed.\n\n"
    )
 
    send_message(header + answers)
    print("Answers sent successfully.")
 
# ── Entry Point ───────────────────────────────────────────────────────────────
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "questions"
    print(f"Running in mode: {mode}")
    try:
        if mode == "questions":
            run_questions()
        elif mode == "answers":
            run_answers()
        else:
            print(f"Unknown mode: {mode}")
            sys.exit(1)
    except Exception as e:
        send_error(mode, e)
        raise
 
if __name__ == "__main__":
    main()
 
