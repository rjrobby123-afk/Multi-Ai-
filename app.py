import streamlit as st
from openai import OpenAI
import time
import uuid


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Multi-AI Super App",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CSS STYLING
# =========================================================

st.markdown("""
<style>

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    color: #777;
    margin-bottom: 25px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# APP TITLE
# =========================================================

st.markdown(
    '<div class="main-title">🤖 Multi-AI Super App</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">একটি প্রশ্ন — স্মার্ট মাল্টি-এআই উত্তর</div>',
    unsafe_allow_html=True
)


# =========================================================
# API CLIENT INITIALIZATION (ChatGPT Only)
# =========================================================

@st.cache_resource
def initialize_client():
    try:
        return OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"]
        )
    except Exception:
        return None

client = initialize_client()


# =========================================================
# SESSION STATE & MULTI-CHAT MANAGEMENT
# =========================================================

if "chats" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.chats = {
        initial_id: {
            "title": "নতুন চ্যাট",
            "history": []
        }
    }
    st.session_state.current_chat_id = initial_id


# =========================================================
# SUPPORTED LANGUAGES
# =========================================================

languages = [
    "Auto Detect",
    "বাংলা",
    "English",
    "हिन्दी",
    "اردو",
    "العربية",
    "中文",
    "Español",
    "Français",
    "Deutsch",
    "Italiano",
    "Português",
    "Русский",
    "日本語",
    "한국어",
    "Türkçe"
]


# =========================================================
# SIDEBAR SETTINGS & CHAT HISTORY
# =========================================================

with st.sidebar:

    st.header("💬 চ্যাট ম্যানেজমেন্ট")

    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {
            "title": "নতুন চ্যাট",
            "history": []
        }
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.divider()

    st.subheader("📚 আগের চ্যাটসমূহ")

    chat_ids = list(st.session_state.chats.keys())
    chat_titles = [st.session_state.chats[cid]["title"] for cid in chat_ids]

    current_index = chat_ids.index(st.session_state.current_chat_id) if st.session_state.current_chat_id in chat_ids else 0

    selected_chat_title = st.radio(
        "আপনার চ্যাট সিলেক্ট করুন",
        chat_titles,
        index=current_index,
        label_visibility="collapsed"
    )

    selected_chat_id = chat_ids[chat_titles.index(selected_chat_title)]
    if selected_chat_id != st.session_state.current_chat_id:
        st.session_state.current_chat_id = selected_chat_id
        st.rerun()

    st.divider()

    st.header("⚙️ Settings")

    selected_language = st.selectbox(
        "🌐 উত্তর দেওয়ার ভাষা",
        languages
    )

    st.divider()

    if st.button(
        "🗑️ Delete Current Chat",
        use_container_width=True
    ):
        if len(st.session_state.chats) > 1:
            del st.session_state.chats[st.session_state.current_chat_id]
            st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
        else:
            st.session_state.chats[st.session_state.current_chat_id] = {
                "title": "নতুন চ্যাট",
                "history": []
            }
        st.rerun()


# Get current active chat data
current_chat = st.session_state.chats[st.session_state.current_chat_id]


# =========================================================
# QUESTION INPUT FORM (Auto-Clear on Submit)
# =========================================================

with st.form(key="ai_question_form", clear_on_submit=True):
    question = st.text_area(
        "💬 আপনার প্রশ্ন লিখুন",
        placeholder=(
            "যেমন:\n"
            "বাংলাদেশের ইতিহাস সম্পর্কে বলো...\n\n"
            "অথবা:\n"
            "পাইথনে একটি লুপ লেখার নিয়ম বুঝিয়ে দাও।"
        ),
        height=140
    )
    
    ask_button = st.form_submit_button(
        "🚀 মাল্টি-এআই কে প্রশ্ন করুন",
        use_container_width=True,
        type="primary"
    )


# =========================================================
# LANGUAGE INSTRUCTION FUNCTION
# =========================================================

def language_instruction(language):

    if language == "Auto Detect":

        return """
Answer in the same language as the user's question.
If multiple languages are used, use the dominant language.
"""

    return f"""
Answer entirely in {language}.
Do not switch to another language unless requested.
"""


# =========================================================
# PROMPT BUILDER (Developer & Brand Identity)
# =========================================================

def build_prompt(question, language):
    return f"""
You are the core intelligence engine of 'Multi-AI Super App'. You were created and developed by Md. Rabby Hossain, who originates from Bangladesh and is currently a student in the Department of Political Science at the University of Barisal. If anyone asks you who created you, who is your developer, or who made you, you must clearly and proudly state that you were created by Md. Rabby Hossain.

{language_instruction(language)}

Answer the user's question accurately, clearly and directly.
Do not invent facts.

User question:
{question}
"""


# =========================================================
# MAIN EXECUTION PROCESS
# =========================================================

if ask_button:

    if not question.strip():

        st.warning(
            "⚠️ দয়া করে একটি প্রশ্ন লিখুন।"
        )

        st.stop()

    if client is None:
        st.error("❌ OpenAI API key পাওয়া যায়নি বা কনফিগারেশন সঠিক নয়।")
        st.stop()

    # Update chat title if it's the first question
    if current_chat["title"] == "নতুন চ্যাট" and question.strip():
        current_chat["title"] = question[:28] + ("..." if len(question) > 28 else "")

    # =====================================================
    # QUERY CHATGPT (Under Multi-AI Branding)
    # =====================================================

    start_time = time.time()

    answer = ""

    with st.spinner("🤖 Multi-AI Super Engine উত্তর তৈরি করছে..."):
        try:
            prompt = build_prompt(question, selected_language)
            response = client.responses.create(
                model="gpt-5.6-luna",
                input=prompt
            )
            answer = response.output_text
        except Exception as e:
            answer = f"❌ Error:\n\n{str(e)}"

    elapsed = round(
        time.time() - start_time,
        2
    )

    # Save to current chat history
    current_chat["history"].append({
        "question": question,
        "answer": answer
    })

    st.success(
        f"✅ উত্তর প্রস্তুত • {elapsed} সেকেন্ড"
    )


# =========================================================
# DISPLAY CHAT HISTORY FOR CURRENT CHAT (Unified Multi-AI Card)
# =========================================================

if current_chat["history"]:

    st.divider()

    for idx, item in enumerate(current_chat["history"]):

        st.markdown(f"### 💬 Q: {item['question']}")

        with st.container(border=True):
            st.subheader("✨ Multi-AI Super Response")
            st.markdown("---")
            st.markdown(item["answer"])
            st.download_button(
                "⬇️ Download Response",
                item["answer"],
                file_name=f"MultiAI_answer_{idx}.txt",
                mime="text/plain",
                use_container_width=True,
                key=f"download_{current_chat}_{idx}"
            )
        
        st.divider()


# =========================================================
# FOOTER
# =========================================================

st.caption(
    "🤖 Multi-AI Super App • Developed by Md. Rabby Hossain"
)
