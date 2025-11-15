import os
import streamlit as st
import pdfplumber
from dotenv import load_dotenv
import google.generativeai as genai

# --- Load Gemini API Key ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("GOOGLE_API_KEY not found in .env")
    st.stop()

genai.configure(api_key=api_key)


# --- Helper function to extract text from PDF ---
@st.cache_data
def extract_pdf_text(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None


# --- Streamlit UI ---
st.set_page_config(page_title="Chat with your PDF", page_icon="📄", layout="wide")
st.title("📄 PDF Chatbot")

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = None
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None

# Upload PDF
pdf_file = st.file_uploader("Upload a PDF", type="pdf")

if pdf_file:
    # Check if a new PDF was uploaded
    if pdf_file.name != st.session_state.pdf_name:
        with st.spinner("Extracting PDF text..."):
            pdf_text = extract_pdf_text(pdf_file)

        if pdf_text:
            st.session_state.pdf_text = pdf_text
            st.session_state.pdf_name = pdf_file.name
            st.session_state.chat_history = []  # Reset chat history for new PDF
            st.success(f"PDF '{pdf_file.name}' loaded successfully!")

    if st.session_state.pdf_text:
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        user_input = st.chat_input("Ask a question about the PDF...")

        if user_input:
            # Add user message to history
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input}
            )

            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)

            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    prompt = f"""
You are a helpful AI assistant. Answer questions based on the provided PDF content. Be concise and accurate.

PDF Content:
{st.session_state.pdf_text}

Question: {user_input}

Answer:
"""
                    try:
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        config = {
                            "temperature": 0.3,
                            "max_output_tokens": 512,
                        }
                        response = model.generate_content(
                            prompt, generation_config=config
                        )

                        # Handle safety blocks or empty responses
                        if response.candidates and response.candidates[0].content.parts:
                            answer = response.text
                            st.markdown(answer)
                            # Add assistant message to history
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": answer}
                            )
                        else:
                            error_msg = "The API blocked the response (safety filter). Try rephrasing your question."
                            st.warning(error_msg)
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": error_msg}
                            )

                    except Exception as e:
                        error_msg = f"Error generating answer: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": error_msg}
                        )
