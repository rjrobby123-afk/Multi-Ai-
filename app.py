import streamlit as st
from google import genai
from google.genai import types
from openai import OpenAI
import concurrent.futures
import time


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
    '<div class="subtitle">একটি প্রশ্ন — একাধিক AI-এর উত্তর</div>',
    unsafe_allow_html=True
)


# =========================================================
# API CLIENTS INITIALIZATION
# =========================================================

@st.cache_resource
def initialize_clients():

    clients = {
        "Gemini": None,
        "ChatGPT": None,
        "Grok": None
    }

    # -------------------------
    # Gemini
    # -------------------------
    try:
        clients["Gemini"] = genai.Client(
            api_key=st.secrets["GEMINI_API_KEY"]
        )
    except Exception:
        pass

    # -------------------------
    # OpenAI / ChatGPT
    # -------------------------
    try:
        clients["ChatGPT"] = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"]
        )
    except Exception:
        pass

    # -------------------------
    # xAI / Grok
    # -------------------------
    try:
        clients["Grok"] = OpenAI(
            api_key=st.secrets["XAI_API_KEY"],
            base_url="https://api.x.ai/v1"
        )
    except Exception:
        pass

    return clients


clients = initialize_clients()


# =========================================================
# SESSION STATE MANAGEMENT
# =========================================================

if "history" not in st.session_state:
    st.session_state.history = []

if "answers" not in st.session_state:
    st.session_state.answers = {}


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
# SIDEBAR SETTINGS
# =========================================================

with st.sidebar:

    st.header("⚙️ Settings")

    selected_language = st.selectbox(
        "🌐 উত্তর দেওয়ার ভাষা",
        languages
    )

    st.divider()

    st.subheader("🤖 AI নির্বাচন")

    use_gemini = st.checkbox(
        "🟦 Gemini",
        value=True
    )

    use_chatgpt = st.checkbox(
        "🟣 ChatGPT",
        value=True
    )

    use_grok = st.checkbox(
        "🟢 Grok",
        value=True
    )

    st.divider()

    if st.button(
        "🗑️ Clear History",
        use_container_width=True
    ):

        st.session_state.history = []
        st.session_state.answers = {}

        st.rerun()


# =========================================================
# QUESTION INPUT FORM (Auto-Clear on Submit)
# =========================================================

with st.form(key="ai_question_form", clear_on_submit=True):
    question = st.text_area(
        "💬 আপনার প্রশ্ন লিখুন",
        placeholder=(
            "যেমন:\n"
            "এই ছবিটা আমাকে বুঝিয়ে দাও।\n\n"
            "অথবা:\n"
            "এই PDF-এর মূল বিষয়গুলো ব্যাখ্যা কর।"
        ),
        height=160
    )
    
    ask_button = st.form_submit_button(
        "🚀 AI-গুলোকে প্রশ্ন করুন",
        use_container_width=True,
        type="primary"
    )


# =========================================================
# FILE UPLOAD SECTION
# =========================================================

uploaded_file = st.file_uploader(
    "📎 ছবি অথবা PDF দিন",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp",
        "heic",
        "heif",
        "pdf"
    ],
    help="ছবি বা PDF দিয়ে সেটি সম্পর্কে প্রশ্ন করতে পারবেন।"
)


# =========================================================
# SHOW UPLOADED FILE PREVIEW
# =========================================================

if uploaded_file:

    st.success(
        f"📎 ফাইল নির্বাচিত: {uploaded_file.name}"
    )

    file_type = uploaded_file.type

    if file_type.startswith("image/"):

        st.image(
            uploaded_file,
            caption="আপনার দেওয়া ছবি",
            use_container_width=True
        )

    elif file_type == "application/pdf":

        st.info(
            "📄 PDF প্রস্তুত। এখন প্রশ্ন লিখে AI-কে জিজ্ঞাসা করুন।"
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
# FILE ANALYSIS BY GEMINI
# =========================================================

def analyze_file_with_gemini(uploaded_file, question, language):

    client = clients["Gemini"]

    if client is None:

        return (
            "File analysis could not be performed "
            "because Gemini API is unavailable."
        )

    try:

        file_bytes = uploaded_file.getvalue()

        uploaded = client.files.upload(
            file=file_bytes,
            config={
                "mime_type": uploaded_file.type,
                "display_name": uploaded_file.name
            }
        )

        prompt = f"""
You are the document/image understanding component of a Multi-AI application created by Md. Rabby Hossain from Bangladesh, who is currently studying in the Department of Political Science at the University of Barisal.

{language_instruction(language)}

Analyze the uploaded file carefully.

The user asks:

{question if question.strip() else "Explain this file clearly."}

Important:
- Read the relevant information from the file.
- Understand images, tables, charts and diagrams when present.
- Do not invent information that is not visible in the file.
- Give a factual description of the information relevant to the user's question.
- This analysis will be passed to other AI systems.
"""

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=[
                uploaded,
                prompt
            ]
        )

        return response.text

    except Exception as e:

        return f"FILE_ANALYSIS_ERROR: {str(e)}"


# =========================================================
# NORMAL PROMPT BUILDER (Developer Context Included)
# =========================================================

def build_prompt(
    question,
    language,
    file_context=None
):

    file_section = ""

    if file_context:

        file_section = f"""

==============================
UPLOADED FILE INFORMATION
==============================

{file_context}

==============================
END FILE INFORMATION
==============================
"""

    return f"""
You are an advanced AI assistant. You were created and developed by Md. Rabby Hossain, who originates from Bangladesh and is currently a student in the Department of Political Science at the University of Barisal. If anyone asks you who created you, who is your developer, or who made you, you must clearly and proudly state that you were created by Md. Rabby Hossain.

{language_instruction(language)}

Answer the user's question accurately, clearly and directly.

Do not invent facts.

If information comes from the uploaded file, base the answer on that information.

User question:

{question}

{file_section}
"""


# =========================================================
# GEMINI RESPONSE FUNCTION
# =========================================================

def ask_gemini(
    question,
    language,
    file_context=None
):

    client = clients["Gemini"]

    if client is None:
        return "❌ Gemini API key পাওয়া যায়নি।"

    try:

        prompt = build_prompt(
            question,
            language,
            file_context
        )

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        return f"❌ Gemini Error:\n\n{str(e)}"


# =========================================================
# CHATGPT RESPONSE FUNCTION
# =========================================================

def ask_chatgpt(
    question,
    language,
    file_context=None
):

    client = clients["ChatGPT"]

    if client is None:
        return "❌ OpenAI API key পাওয়া যায়নি।"

    try:

        prompt = build_prompt(
            question,
            language,
            file_context
        )

        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )

        return response.output_text

    except Exception as e:

        return f"❌ ChatGPT Error:\n\n{str(e)}"


# =========================================================
# GROK RESPONSE FUNCTION
# =========================================================

def ask_grok(
    question,
    language,
    file_context=None
):

    client = clients["Grok"]

    if client is None:
        return "❌ Grok API key পাওয়া যায়নি।"

    try:

        prompt = build_prompt(
            question,
            language,
            file_context
        )

        response = client.responses.create(
            model="grok-4.6",
            input=prompt
        )

        return response.output_text

    except Exception as e:

        return f"❌ Grok Error:\n\n{str(e)}"


# =========================================================
# MAIN EXECUTION PROCESS
# =========================================================

if ask_button:

    if not question.strip() and not uploaded_file:

        st.warning(
            "⚠️ একটি প্রশ্ন লিখুন অথবা একটি ছবি/PDF দিন।"
        )

        st.stop()

    selected_functions = {}

    if use_gemini:
        selected_functions["Gemini"] = ask_gemini

    if use_chatgpt:
        selected_functions["ChatGPT"] = ask_chatgpt

    if use_grok:
        selected_functions["Grok"] = ask_grok

    if not selected_functions:

        st.warning(
            "⚠️ অন্তত একটি AI নির্বাচন করুন।"
        )

        st.stop()


    # =====================================================
    # FILE ANALYSIS EXECUTION
    # =====================================================

    file_context = None

    if uploaded_file:

        with st.spinner(
            "📄 ছবি/PDF বিশ্লেষণ করা হচ্ছে..."
        ):

            file_context = analyze_file_with_gemini(
                uploaded_file,
                question,
                selected_language
            )


    # =====================================================
    # PARALLEL AI QUERY EXECUTION
    # =====================================================

    results = {}

    start_time = time.time()

    with st.spinner(
        "🤖 AI-গুলো উত্তরগুলো তৈরি করছে..."
    ):

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(selected_functions)
        ) as executor:

            future_map = {}

            for name, function in selected_functions.items():

                future = executor.submit(
                    function,
                    question,
                    selected_language,
                    file_context
                )

                future_map[future] = name


            for future in concurrent.futures.as_completed(
                future_map
            ):

                name = future_map[future]

                try:

                    results[name] = future.result()

                except Exception as e:

                    results[name] = (
                        f"❌ {name} Error:\n\n{str(e)}"
                    )


    elapsed = round(
        time.time() - start_time,
        2
    )

    st.session_state.answers = results

    st.session_state.history.append({
        "question": question,
        "file": uploaded_file.name
        if uploaded_file else None,
        "answers": results
    })


    st.success(
        f"✅ উত্তর পাওয়া গেছে • {elapsed} সেকেন্ড"
    )


# =========================================================
# DISPLAY ANSWERS IN CARD / BOX LAYOUT
# =========================================================

if st.session_state.answers:

    st.divider()

    st.subheader("🧠 AI Responses")

    results = st.session_state.answers

    columns = st.columns(
        len(results)
    )

    icons = {
        "Gemini": "🟦",
        "ChatGPT": "🟣",
        "Grok": "🟢"
    }

    for index, (name, answer) in enumerate(
        results.items()
    ):

        with columns[index]:
            # প্রতিটি এআই-এর উত্তর সুন্দর বক্স বা কার্ডের ভেতর দেখানোর জন্য
            with st.container(border=True):

                st.subheader(
                    f"{icons.get(name, '🤖')} {name}"
                )

                st.markdown("---")

                st.markdown(answer)

                st.download_button(
                    "⬇️ Download",
                    answer,
                    file_name=f"{name}_answer.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key=f"download_{name}_{index}"
                )


# =========================================================
# PREVIOUS QUESTIONS HISTORY
# =========================================================

if st.session_state.history:

    st.divider()

    with st.expander(
        f"📚 Previous Questions ({len(st.session_state.history)})"
    ):

        for i, item in enumerate(
            reversed(st.session_state.history),
            1
        ):

            st.markdown(
                f"**{i}. {item['question'] or 'File analysis'}**"
            )

            if item["file"]:

                st.caption(
                    f"📎 {item['file']}"
                )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🤖 Multi-AI Super App • Gemini + ChatGPT + Grok"
)
