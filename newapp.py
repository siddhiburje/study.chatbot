import streamlit as st
import requests
from datetime import datetime

if 'flashcards' not in st.session_state:
    st.session_state.flashcards = None

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Study Chatbot",
    page_icon="🎓",
    layout="wide"
)

# ---------------- HUGGING FACE ----------------
HF_URL = "https://router.huggingface.co/v1/chat/completions"

HF_HEADERS = {
    "Authorization": f"Bearer {st.secrets['HF_KEY']}",
    "Content-Type": "application/json"
}

MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"


def query_hf(messages):
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 800
    }

    try:
        r = requests.post(HF_URL, headers=HF_HEADERS, json=payload, timeout=60)

        if r.status_code != 200:
            return f"HTTP Error {r.status_code}: {r.text}"

        data = r.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Error: {str(e)}"


# ---------------- STYLE (RESTORED + ENHANCED COLORS) ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background: radial-gradient(circle at center, #100827 0%, #000000 80%);
    color: #f5d0fe;
}

/* HEADER */
.header {
    font-size: 48px;
    font-weight: 700;
    background: linear-gradient(135deg, #f5d0fe, #c084fc, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subheader {
    color: #e9d5ff;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: rgba(15, 7, 32, 0.6);
    backdrop-filter: blur(12px);
}

/* CHAT */
.chat-container {
    display: flex;
    flex-direction: column;
}

/* USER = RIGHT SIDE */
.user-msg {
    background: rgba(236,72,153,0.14); /* 🔥 slightly lighter than bot (0.10 → 0.14) */

    padding: 12px 15px;
    border-radius: 18px 18px 4px 18px;

    max-width: 70%;
    margin: 10px 0 10px auto;

    color: #ffffff;

    text-align: left;
}

/* BOT = LEFT SIDE */
.bot-msg {
    background: rgba(236,72,153,0.10);

    padding: 12px 15px;
    border-radius: 18px 18px 18px 4px;

    max-width: 70%;
    margin: 10px auto 10px 0;

    color: #ffffff;

    text-align: left;
}

.user-msg, .bot-msg {
    word-wrap: break-word;
    white-space: pre-wrap;
}


/* FLASHCARD UI */
.flashcard-ui {
    background: #FFF0F5; /* Lavender Blush */
    background: linear-gradient(135deg, #fff5f8 0%, #ffe4e1 100%);
    width: 100%;
    min-height: 180px;
    height: 280px;            /* Set a fixed height */
    overflow-y: auto;         /* Add a tiny scroll if text is too long */
    display: flex;
    flex-direction: column;
    padding: 20px;
    margin: 10px 0;
    border-radius: 25px;
    border: 3px solid #ffb6c1; /* Pastel Pink Border */
    box-shadow: 5px 5px 0px #ffdae0;
    display: flex;
    flex-direction: column;
    transition: transform 0.2s ease;
}


.flashcard-ui:hover {
    transform: scale(1.02);
}

.flash-badge {
    font-family: 'Fredoka', sans-serif;
    font-size: 12px;
    color: #db2777;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 8px;
}

.flash-term {
    font-size: 20px;
    font-weight: 700;
    color: #4a044e; /* Dark Purple Text */
    font-family: 'Fredoka', sans-serif;
    margin-bottom: 8px;
}

.flash-def {
    font-size: 15px;
    color: #5b21b6;
    line-height: 1.4;
    font-family: 'Quicksand', sans-serif;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "persona" not in st.session_state:
    st.session_state.persona = "Helpful Assistant"


# ---------------- PERSONA ENGINE (FIXED STRONG CONTROL) ----------------
def get_system_prompt():
    base = "You are a highly intelligent college AI assistant."

    personas = {
        "Teacher": base + """ You are a teacher-style assistant whose purpose is to explain concepts clearly, guide learning step by step, and help the user build strong understanding. Your tone should be calm, patient, and structured, like a good classroom teacher. Focus on clarity over speed, and break down complex ideas into simple, logical parts. Use examples, analogies, and step-by-step reasoning when needed to make concepts easier to understand. Encourage the user to think and participate by asking guiding questions, but always remain supportive and constructive. If the user makes mistakes, correct them clearly and explain why the answer is wrong, then show the correct approach. Avoid being overly casual or humorous unless it helps understanding. Stay focused on teaching the concept thoroughly and ensuring the user actually learns, not just receives answers.""",
        "Funny Friend": base + """ You are a funny, friendly assistant who chats like a playful and entertaining friend. Your goal is to make conversations enjoyable while still being helpful when needed. Use a light, humorous tone, including jokes, witty remarks, and casual language where appropriate, but never at the cost of clarity or correctness. Keep responses engaging and relatable, as if you are talking to a close friend. Avoid being rude, offensive, or overly sarcastic, and make sure your humor is always safe and positive. If the user asks serious or complex questions, shift smoothly into a helpful mode while still keeping a friendly, upbeat vibe. Balance fun and usefulness so the user feels both entertained and supported in the conversation.""",
        "Strict Tutor": base + """ You are a strict tutor designed to help the user learn through discipline, precision, and accountability. Your role is to teach clearly, correct mistakes directly, and push the user toward accurate understanding without unnecessary softness or casual conversation. Maintain a firm, serious, and focused tone at all times. Do not overpraise or comfort the user; instead, emphasize correctness, effort, and improvement. When the user makes mistakes, point them out clearly and explain the correct concept step by step. Expect the user to think and engage—ask challenging follow-up questions when appropriate and do not give answers too easily if the user is clearly meant to learn. Keep explanations structured, logical, and concise, prioritizing understanding over friendliness. If the user is incorrect, correct them firmly but respectfully, ensuring they understand why. Always stay on topic, avoid distractions, and guide the user toward mastery of the subject.""",
        "Helpful Assistant": base + """ You are a helpful assistant designed to support the user by providing clear, accurate, and useful responses. Your primary goal is to assist with questions and tasks efficiently while keeping explanations simple and easy to understand. Maintain a friendly and professional tone, avoiding unnecessary complexity or overly long responses unless the user requests more detail. If a question is unclear, ask a brief clarifying question before answering. Always prioritize correctness, and if you are unsure about something, acknowledge the limitation instead of guessing. Stay focused on the user’s request and avoid irrelevant information. Be respectful and neutral in all interactions, and ensure your responses are safe, responsible, and appropriate."""
    }

    return personas.get(st.session_state.persona, base)


# ---------------- FEATURE ENGINE ----------------
def run_feature(mode):

    context_list = []
    greetings = ["hi", "hello", "hey", "hola", "chatbot", "hi chatbot", "hey there", "hello!", "hi!"]
    
    for m in st.session_state.messages[-10:]:
        content = m["content"]
        # Only grab content if it is TEXT (prevents the 'list' crash)
        if isinstance(content, str):
            # Only grab content if it's NOT a greeting
            clean_content = content.lower().strip().strip('!?.')
            if content.lower().strip() not in greetings and len(clean_content) > 5:
                context_list.append(content)
             #-------last_chat = "\n".join(context_list) [m["content"] for m in st.session_state.messages[-6:]]----
    last_chat = "\n\n".join(context_list[-3:])

    if not last_chat.strip():
        st.error("Wait! There's no study material in the chat yet. Type or paste some notes first!")
        return

    if mode == "flashcards":
        messages = [
            {"role": "system", "content": """You output ONLY structured flashcards. CRITICAL RULE: Ignore all greetings or introductory small talk. 
                ONLY process the text if it contains educational facts. 
                If the input is just small talk, do NOT generate a card. 
                Instead, reply ONLY with: 'ERROR: NO CONTENT'.
                Format for valid cards: Term: [term] Definition: [definition]"""},
            {"role": "user", "content": f"Create 3 flashcards based on this info: {last_chat}"}
        ]

        reply = query_hf(messages)

        if "ERROR" in reply.upper() or "NO CONTENT" in reply.upper():
            st.warning("I need actual facts to make cards. Try pasting some study notes!")
            return
        
        cards_data = []
        raw_cards = reply.split("Term:")
        for block in raw_cards:
            if "Definition:" in block:
                term_part, def_part = block.split("Definition:", 1)
                cards_data.append({"term": term_part.strip(), "def": def_part.strip()})
        
        if cards_data:
            st.session_state.messages.append({"role": "assistant", "type": "flashcards", "content": cards_data})


    elif mode == "eli5":
        messages = [
            {"role": "system", "content": "Explain simply like to a child."},
            {"role": "user", "content": last_chat}
        ]
        reply = query_hf(messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})

    elif mode == "citations":
        messages = [
            {"role": "system", "content": "Generate APA citations only."},
            {"role": "user", "content": last_chat}
        ]
        reply = query_hf(messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})


# ---------------- SIDEBAR (RESTORED STRUCTURE) ----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=60)
    st.title("Other Options")

    st.subheader("AI Personas")
    st.session_state.persona = st.radio(
        "Select Tone:",
        ["Helpful Assistant", "Teacher", "Funny Friend", "Strict Tutor"]
    )

    st.markdown("---")

    st.subheader("Study Session")
    c1, c2 = st.columns(2)

    with c1:
        if st.button("Start 25 min"):
            st.toast("Timer Started")

    with c2:
        if st.button("Reset"):
            st.toast("Reset Done")

    st.markdown("---")

    st.subheader("Brain Power")
    st.progress(min(len(st.session_state.messages) / 20, 1.0))


    if st.button("Wipe Chat"):
        st.session_state.messages = []
        st.rerun()


# ---------------- HEADER ----------------
st.markdown("<div class='header'>Study Chatbot</div>", unsafe_allow_html=True)
st.markdown("<div class='subheader'>The ultimate academic companion for the modern student.</div>", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)


# ---------------- INPUT ----------------
user_input = st.chat_input("Ask anything regarding calculus, physics or any other subject...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    api_messages = [{"role": "system", "content": get_system_prompt()}]
    
    for m in st.session_state.messages:
        if "type" not in m and isinstance(m["content"], str):
            api_messages.append({"role": m["role"], "content": m["content"]})

    reply = query_hf(api_messages)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()


# ---------------- CHAT ----------------
for msg in st.session_state.messages:
    if msg.get("type") == "flashcards":
        # This renders the cute pastel cards
        cols = st.columns(3)
        for i, card in enumerate(msg["content"]):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="flashcard-ui">
                    <div class="flash-badge">✨ STUDY CARD</div>
                    <div class="flash-term">{card['term']}</div>
                    <div class="flash-def">{card['def']}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        # This renders the normal chat bubbles
        cls = "user-msg" if msg["role"] == "user" else "bot-msg"
        st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)


# ---------------- TOOLBELT ----------------
st.markdown("## 👩🏼‍🎓 Academic Toolbelt")

c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("Generate Flashcards"):
        run_feature("flashcards")
        st.rerun()

with c2:
    if st.button("Simplify Topic"):
        run_feature("eli5")
        st.rerun()

with c3:
    if st.button("Cite Sources"):
        run_feature("citations")
        st.rerun()

#---- with c4: export_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])  st.download_button("Export Study Notes", export_text, file_name="study_notes.txt")-------

with c4:
    export_list = []
    
    for m in st.session_state.messages:
        role_label = m['role'].upper()
        
        # Check if the content is a list (Flashcards)
        if isinstance(m["content"], list):
            # Format the list of dictionaries into a readable string block
            cards_text = [f"📇 Term: {card['term']}\n   Definition: {card['def']}" for card in m["content"]]
            formatted_cards = "\n".join(cards_text)
            export_list.append(f"--- {role_label} (FLASHCARDS) ---\n{formatted_cards}")
        
        # Otherwise, treat it as a normal string (User or Bot text)
        else:
            export_list.append(f"--- {role_label} ---\n{m['content']}")
            
    # Combine everything with double newlines for readability
    export_text = "\n\n".join(export_list)
    
    st.download_button(
        label="Export Study Notes",
        data=export_text,
        file_name=f"study_notes_{datetime.now().strftime('%Y-%m-%d')}.txt",
        mime="text/plain"
    )