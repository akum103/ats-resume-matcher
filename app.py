import fitz
from docx import Document
import streamlit as st
from openai import OpenAI
import pandas as pd
import re
from io import StringIO
import os

# --- Streamlit Page Config ---
st.set_page_config(page_title="ATS Resume Matcher", layout="centered")

# --- Select User ---
user = st.selectbox("👤 Select User", ["Ankit", "Medha"])
st.markdown(f"Hello, **{user}**! Let's tailor your resume. 🧠")

# --- API Key ---
api_key = st.text_input("🔑 Enter your OpenAI API Key", type="password")
if not api_key:
    st.warning("Please enter your OpenAI API key to continue.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- Text Extractors ---
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "\n".join([page.get_text() for page in doc])

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# --- GPT Resume Scoring Prompt ---
def get_ats_score(resume, jd):
    prompt = f"""
I am applying for a job and want to optimize my resume for better alignment with the job description. Follow these structured steps to analyze, compare, and refine my resume while keeping it natural and ATS-friendly.

1. Extract all Responsibilities & Qualifications:
o Identify and highlight all responsibilities and qualifications from the provided job description.
o Summarize them concisely in a structured manner.

2. Mismatch Analysis (Tabular Format):
o Compare my resume against the job qualifications line by line for required and preferred qualifications.
o Present the results in a table format with these columns:
   Column 1: Job Qualification (from JD)
   Column 2: My Resume’s Matching Experience with percentage
   Column 3: Match or No Match (Yes/No)
✅ Use markdown syntax to format the mismatch table. Do not use bullet points or paragraph explanations.

Dont forget to give approximate ATS Score

3. Experience Refinement (Bullet Point Adjustments):
for this, only use my work experience.
o Modify my previous experience to better match the job description.
o Ensure the changes sound natural and human-like, avoiding exaggeration while enhancing relevance.
o Present each bullet point modification in a structured format:
   Column 1: Company Name
   Column 2: Original Bullet
   Column 3: Modified Bullet
   Column 4: Reason for Change

✅ Use markdown syntax to format the mismatch table. Do not use bullet points or paragraph explanations.

4. Change Log for Bullet Points:
o Track all modifications made in the experience section.
o Do not change too much—just enough to pass ATS filters while keeping my resume realistic and authentic.

5. Skills Section Enhancement:
o Suggest changes to my skills section by adding, rewording, or adjusting skills to align with the job description.
o Give as many skills as possible
o Prioritize industry-relevant keywords while ensuring my expertise remains credible.

📌 Important Notes:
• Keep changes minimal yet impactful to pass ATS without making my resume feel unnatural.
• Focus on keyword optimization rather than drastic modifications.
• Maintain a human tone in all modifications.

Now, provide the analysis and refinement based on the attached job description and resume.

{jd}

Resume:
{resume}
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content

# --- Save Resume File (as text) for user ---
def save_user_resume(user, resume_text):
    with open(f"{user.lower()}_resume.txt", "w", encoding="utf-8") as f:
        f.write(resume_text)

def load_user_resume(user):
    path = f"{user.lower()}_resume.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None

# --- UI Section ---
jd_input = st.text_area("📄 Paste Job Description here")

uploaded_file = st.file_uploader("📎 Upload Your Resume (.docx or .pdf)", type=["pdf", "docx"])

# --- Use Last Resume Button ---
resume_text = ""
if st.button("📂 Use Last Uploaded Resume"):
    saved = load_user_resume(user)
    if saved:
        resume_text = saved
        st.success(f"✅ Loaded last resume for {user}")
    else:
        st.warning("No resume found. Please upload one.")

# --- Upload Resume & Analyze ---
if uploaded_file and not resume_text:
    resume_text = extract_text_from_pdf(uploaded_file) if uploaded_file.name.endswith(".pdf") else extract_text_from_docx(uploaded_file)
    save_user_resume(user, resume_text)
    st.success("📥 Resume uploaded and saved!")

if st.button("🔍 Analyze Resume"):
    if not resume_text or not jd_input.strip():
        st.warning("Please provide both resume and job description.")
    else:
        with st.spinner("Analyzing..."):
            result = get_ats_score(resume_text, jd_input)
            st.success("✅ Analysis Complete!")

            st.markdown("### 📝 Full GPT Response")
            st.markdown(result)
