from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pdf_utils import extract_pdf_text
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PDF_TEXT = ""  # in-memory storage


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global PDF_TEXT
    PDF_TEXT = extract_pdf_text(file.file)
    return {"message": "PDF uploaded & processed successfully."}


@app.post("/ask")
async def ask_question(question: str = Form(...)):
    if not PDF_TEXT:
        return {"answer": "Please upload a PDF first."}

    prompt = f"""
    You are an AI assistant. Answer the question using ONLY this PDF text:

    PDF Content:
    {PDF_TEXT}

    Question: {question}
    Answer:
    """

    response = genai.generate_text(model="gemini-1.5-flash", prompt=prompt)

    return {"answer": response.text}
