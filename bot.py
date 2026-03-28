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
    "gemini-1.5-flash",
]

# ── Case Study Scenario Types (rotates daily) ─────────────────────────────────
CASE_STUDY_TYPES = [
    "civil servant facing political pressure to bend rules for a powerful politician",
    "IAS officer discovering corruption by a senior colleague during disaster relief",
    "district collector caught between orders from state government and welfare of tribal community",
    "IPS officer facing dilemma of exposing a scam that implicates his own department",
    "civil servant whose family member is involved in a case under his own jurisdiction",
    "officer managing communal tension where political masters want biased action",
    "bureaucrat pressured to manipulate data in a government welfare scheme report",
]

# ── Topic Rotation with PYQ Themes ───────────────────────────────────────────
GS1_TOPICS = [
    {
        "topic": "Indian Society: Diversity, Social Stratification and Caste",
        "pyq_themes": [
            "Caste as a social institution vs political mobilisation tool",
            "Sanskritisation and Westernisation — M.N. Srinivas",
            "Social mobility and structural barriers in Indian society",
            "Reservation policy and its impact on social justice",
            "Intersection of caste, class and gender in India",
        ]
    },
    {
        "topic": "Role of Women: Empowerment, Violence and Representation",
        "pyq_themes": [
            "Feminisation of poverty — causes and consequences",
            "Self Help Groups as instruments of women empowerment",
            "Women in political representation — 33% reservation debate",
            "Domestic violence, POCSO and legal safeguards",
            "Gender gap in workforce participation — LFPR data NFHS-5",
        ]
    },
    {
        "topic": "Communalism, Regionalism and Secularism",
        "pyq_themes": [
            "Constitutional secularism vs Western secularism",
            "Communalism as a political mobilisation tool in India",
            "Regionalism — threat or opportunity for national integration",
            "Role of media in amplifying communal narratives",
            "Composite culture and syncretic traditions of India",
        ]
    },
    {
        "topic": "Population: Demographic Dividend, Ageing and Migration",
        "pyq_themes": [
            "Demographic dividend — preconditions and risks of missing it",
            "Ageing population and social security challenges in India",
            "Rural to urban migration — push pull factors and consequences",
            "Population policy beyond fertility control",
            "Brain drain vs brain gain — Indian diaspora debate",
        ]
    },
    {
        "topic": "Poverty, Social Exclusion and Inclusive Growth",
        "pyq_themes": [
            "Multidimensional poverty beyond income — MPI India 2023",
            "Social exclusion of Scheduled Tribes and Dalits",
            "Role of MGNREGA in rural poverty alleviation",
            "Inclusive growth vs trickle down economics debate",
            "Linkage between poverty, education and social mobility",
        ]
    },
    {
        "topic": "Urbanisation: Smart Cities, Slums and Governance",
        "pyq_themes": [
            "Slum formation as a consequence of governance failure",
            "Smart Cities Mission — promise vs ground reality",
            "Urban local bodies and 74th Constitutional Amendment",
            "Push pull factors of rural to urban migration",
            "Urban waste management and environmental challenges",
        ]
    },
    {
        "topic": "Globalisation and Its Impact on Indian Society",
        "pyq_themes": [
            "Cultural homogenisation vs cultural diversity under globalisation",
            "Globalisation and widening income inequality in India",
            "Impact on Indian family structure — rise of nuclear families",
            "Gig economy and changing nature of work and labour rights",
            "Globalisation and women — empowerment or new forms of exploitation",
        ]
    },
]

GS4_TOPICS = [
    {
        "topic": "Ethics and Human Interface: Determinants of Ethical Behaviour",
        "pyq_themes": [
            "Role of family, society and education in value formation",
            "Influence of religion and culture on ethical behaviour",
            "Conscience as moral guide vs conformity to social norms",
            "Moral relativism vs universal ethics in governance",
            "Ethics of care — Gilligan's framework in public service",
        ]
    },
    {
        "topic": "Attitude: Formation, Change and Social Influence",
        "pyq_themes": [
            "Cognitive dissonance and attitude change in administrators",
            "Role of attitude in ethical administrative decision making",
            "Prejudice and stereotyping — impact on governance",
            "Social influence on individual moral choices",
            "Moral courage to challenge wrong institutional attitudes",
        ]
    },
    {
        "topic": "Civil Services Values: Integrity, Impartiality and Empathy",
        "pyq_themes": [
            "Integrity beyond legal compliance — spirit vs letter of law",
            "Impartiality when political pressure conflicts with duty",
            "Empathy as foundation of public service delivery",
            "Dedication to public service vs personal career advancement",
            "Objectivity and evidence based policy making",
        ]
    },
    {
        "topic": "Emotional Intelligence in Governance",
        "pyq_themes": [
            "Self awareness and self regulation in crisis management",
            "Empathy as a tool for inclusive administration",
            "Emotional intelligence vs IQ in leadership effectiveness",
            "Managing stress and preventing burnout in civil services",
            "EI in conflict resolution and building effective teams",
        ]
    },
    {
        "topic": "Moral Thinkers: Gandhi, Ambedkar, Aristotle and Kant",
        "pyq_themes": [
            "Gandhian ethics — trusteeship and non violence in governance",
            "Ambedkar — constitutional morality vs social morality",
            "Kant's categorical imperative applied to public administration",
            "Aristotle's virtue ethics — character of an ideal civil servant",
            "Kautilya's Arthashastra — relevance to modern governance",
        ]
    },
    {
        "topic": "Probity in Governance: Transparency and Accountability",
        "pyq_themes": [
            "RTI Act as a fundamental tool of democratic accountability",
            "Whistleblower protection and ethics of institutional dissent",
            "Conflict of interest — identification and management in public office",
            "Ethical dilemmas of loyalty to institution vs public interest",
            "Citizen's charter and ethics of public service delivery",
        ]
    },
    {
        "topic": "Ethical Dilemmas in Administration: Theory and Application",
        "pyq_themes": [
            "Conflict between orders from superior and public welfare",
            "Ethical dimensions of corruption and duty to report",
            "Disaster management — ethical allocation of limited resources",
            "Political interference in transfers and postings",
            "Handling confidential government information ethically",
        ]
    },
]

def today_topics():
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    day = ist.timetuple().tm_yday
    gs1 = GS1_TOPICS[day % len(GS1_TOPICS)]
    gs4 = GS4_TOPICS[day % len(GS4_TOPICS)]
    case_type = CASE_STUDY_TYPES[day % len(CASE_STUDY_TYPES)]
    return gs1, gs4, case_type, ist.strftime("%d %b %Y")

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
                    break
                print(f"{model} attempt {attempt+1} failed: {e}")
                if attempt == 0:
                    time.sleep(15)
    raise RuntimeError("All models exhausted. Check your Gemini API quota.")

# ── Question Prompt ───────────────────────────────────────────────────────────
QUESTION_PROMPT = """You are a senior UPSC Mains paper setter with 20 years of experience.
You have studied all UPSC GS-1 and GS-4 papers from 2013 to 2024 in detail.

TODAY'S TOPICS:
GS-1 (Society): {gs1_topic}
PYQ Themes: {gs1_themes}

GS-4 (Ethics): {gs4_topic}
PYQ Themes: {gs4_themes}

Today's Case Study Scenario Type: {case_type}

YOUR TASK:
Generate exactly 6 questions as specified below.
Do NOT copy previous year questions directly.
Frame fresh questions inspired by the PYQ themes.

OUTPUT FORMAT (plain text only, no asterisks, no symbols, no markdown):

========================================
GS-1 SOCIETY: {gs1_topic}
========================================

Q1. (10 Marks | 150 words)
[Write one analytical question of 2-3 sentences.
Must test conceptual understanding and analytical ability, not memory recall.
Draw inspiration from PYQ themes but use completely fresh wording.
Style: "Examine the...", "Discuss the...", "Analyse the role of..."]

Q2. (10 Marks | 150 words)
[Write one different conceptual question of 2-3 sentences.
Must approach the topic from a different angle than Q1.
Style: "What do you understand by...", "How has... shaped...", "Critically examine..."]

Q3. (15 Marks | 250 words)
[Write one question of 3-4 sentences requiring multi-dimensional analysis.
Must demand coverage of at least 3 dimensions: social, economic, political, gender or legal.
Style: "Critically analyse...", "Examine the... in the context of...", "Discuss... with suitable examples."]

========================================
GS-4 ETHICS: {gs4_topic}
========================================

Q4. (10 Marks | 150 words)
[Write one conceptual ethics theory question of 2-3 sentences.
Must test understanding of ethical concepts, values and philosophical ideas.
Must relate to civil services or governance context.
Style: "What do you understand by...", "Explain the significance of...", "How does... influence..."]

Q5. (10 Marks | 150 words)
[Write one applied ethics question of 2-3 sentences.
Must require application of ethical concepts to real life administrative situations.
Different angle from Q4.
Style: "How should a civil servant...", "Examine the ethical dimensions of...", "What are the challenges of..."]

Q6. (20 Marks | 300 words) — CASE STUDY
[Write a full UPSC-style case study exactly as follows:

Paragraph 1 — Background and Context (3-4 lines):
Introduce the civil servant by name (use Indian name), designation, department and location.
Describe the work situation and background in specific detail.

Paragraph 2 — The Dilemma (3-4 lines):
Describe the ethical conflict that arises — involve the scenario type: {case_type}.
Show pressure from multiple sides: superior, political leader, public, institution or family.
Make the dilemma realistic, complex and specific — not generic.

Paragraph 3 — Stakeholders and Consequences (2-3 lines):
Mention who will be affected by the officer's decision and in what way.
Show that both action and inaction have serious consequences.

Sub-questions (exactly as UPSC format):
(a) Identify and discuss the ethical issues involved in this case. (50 words)
(b) What are the options available to [officer name]? Evaluate each option with its merits and demerits. (100 words)
(c) What course of action would you recommend and why? How would you handle the pressures involved? (150 words)]

STRICT RULES:
- Follow the marks and word limits exactly as specified above
- No sub-parts for Q1 to Q5
- Case study must be detailed and realistic — not a one-liner
- Plain text only — absolutely no asterisks, hashtags or symbols
- Questions must be analytical, not factual recall
- Each question must approach the topic from a different angle
"""

# ── Answer Prompt ─────────────────────────────────────────────────────────────
ANSWER_PROMPT = """You are a UPSC Mains topper and expert answer writer.
You have scored above 130 in GS-1 and GS-4. Write model answers for all 6 questions below.

ANSWER STRUCTURE FOR Q1 TO Q5:

Q[number]. [Topic] | [Marks] | [Word Limit]

INTRODUCTION:
[2-3 lines. Choose one style:
- Powerful quote by Gandhi, Ambedkar, Aristotle, Kant or a Supreme Court judgment
- Shocking fact or data point that defines the problem
- Constitutional article or SDG goal linkage
- Aspirational or futuristic opening line
Never start with "In India..." or "Since ancient times..." or "It is said that..."]

BODY:
[Numbered points with CAPITAL HEADING on its own line.
Under each heading: 2 crisp lines of explanation using UPSC keywords.
Then: one specific Indian example — name the scheme, case, committee, state or year.
Number of points by marks:
- 10 marks: 3 points
- 15 marks: 5 points]

WAY FORWARD: (include only where policy reform or future action is relevant)
- 3 specific bullet points
- Link to committees, NEP 2020, SDG goals, Vision India 2047, or government schemes

CONCLUSION:
[1-2 lines. Choose one style:
- SDG goal linkage with specific goal number
- Vision India 2047 or Amrit Kaal reference
- Futuristic or aspirational closing
- Relevant quote
Never repeat the introduction.]

---

ANSWER STRUCTURE FOR Q6 CASE STUDY (20 Marks | 300 words):

Q6. Case Study | 20 Marks | 300 words

INTRODUCTION:
[2 lines identifying the core ethical conflict in the case.]

(a) ETHICAL ISSUES INVOLVED: (50 words)
[List ethical issues as numbered points:
1. [Issue name]: one line explanation
2. [Issue name]: one line explanation
3. [Issue name]: one line explanation
Cover: conflict of interest, integrity, loyalty vs public interest, moral courage, probity]

(b) OPTIONS AVAILABLE TO [OFFICER NAME]: (100 words)
[List each option clearly:
Option 1 — [Action]: Merit: ... Demerit: ...
Option 2 — [Action]: Merit: ... Demerit: ...
Option 3 — [Action]: Merit: ... Demerit: ...
Evaluate honestly — no option is perfect]

(c) RECOMMENDED COURSE OF ACTION: (150 words)
[Clearly state which option you recommend and why.
Show how to handle each pressure mentioned in the case.
Reference: Nolan Principles / ARC recommendations / relevant Supreme Court judgment.
End with how this upholds constitutional values and public trust.]

CONCLUSION:
[1-2 lines. Quote or value-based closing on ethical governance.]

---

WORD LIMITS (strictly follow):
- 10-mark answer: 150 words
- 15-mark answer: 250 words
- 20-mark case study: 300 words total across all sub-parts

DIMENSIONS TO COVER:
GS-1 Society: Social / Economic / Political / Gender / Legal / Regional / Data / Global comparison
GS-4 Ethics: Individual ethics / Institutional ethics / Constitutional morality /
             Philosophical backing (Gandhi, Kant, Aristotle, Ambedkar) /
             Emotional intelligence / Governance reform / Stakeholder impact

UPSC KEYWORDS — USE NATURALLY:
GS-1: social capital, demographic dividend, feminisation of poverty, social mobility,
      constitutional morality, majoritarianism, composite culture, intersectionality,
      social stratification, inclusive growth, SDG-1, SDG-5, SDG-10
GS-4: moral courage, conflict of interest, probity, public trust, value pluralism,
      whistleblower, consequentialism, deontological ethics, categorical imperative,
      Nolan principles, emotional intelligence, constitutional ethics,
      ARC recommendations, fiduciary duty

DATA TO CITE WHERE RELEVANT:
NFHS-5 (2021), NCRB 2023, Economic Survey 2024, Census 2011,
World Bank Report, UNDP HDI 2024, MoSPI, ILO Report 2023,
Supreme Court judgments, CAG reports, SECC data

LANGUAGE RULES:
- Simple and direct English — avoid complex vocabulary
- Every sentence must add value — no filler phrases allowed
- Plain text only — no asterisks, hashtags or markdown symbols
- Indian examples must be specific — name the scheme, officer, state or year
- Answers must feel like a topper wrote them — structured, confident, precise

QUESTIONS TO ANSWER:
{questions}
"""

# ── Files ─────────────────────────────────────────────────────────────────────
QUESTIONS_FILE = "latest_questions.txt"
META_FILE      = "latest_meta.json"

# ── Morning: Send Questions ───────────────────────────────────────────────────
def run_questions():
    gs1, gs4, case_type, date_str = today_topics()
    print(f"GS1: {gs1['topic']} | GS4: {gs4['topic']}")

    prompt = QUESTION_PROMPT.format(
        gs1_topic  = gs1["topic"],
        gs1_themes = "\n- ".join(gs1["pyq_themes"]),
        gs4_topic  = gs4["topic"],
        gs4_themes = "\n- ".join(gs4["pyq_themes"]),
        case_type  = case_type,
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
        f"Total: 6 Questions | 75 Marks\n"
        f"Q1, Q2 — 10M each (Society)\n"
        f"Q3     — 15M (Society)\n"
        f"Q4, Q5 — 10M each (Ethics Theory)\n"
        f"Q6     — 20M Case Study (Ethics)\n\n"
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
            "Check if the 8 AM workflow ran and committed latest_questions.txt."
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
        f"Compare with your answers.\n"
        f"Focus on dimensions and examples you missed.\n\n"
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
