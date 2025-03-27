import fitz  # PyMuPDF for PDFs
from docx import Document
import streamlit as st
from openai import OpenAI
import pandas as pd
import re
from io import StringIO

# --- Streamlit UI setup ---
st.set_page_config(page_title="ATS Resume Matcher", layout="centered")
st.title("📊 ATS Resume Match Score Tool")
st.markdown("Upload your resume and paste a job description to get an AI-powered match score.")

# --- Ask for API Key ---
api_key = st.text_input("🔑 Enter your OpenAI API Key", type="password")

if not api_key:
    st.warning("Please enter your OpenAI API key to continue.")
    st.stop()

# --- Initialize OpenAI client securely ---
client = OpenAI(api_key=api_key)

# --- Extract Text from Files ---
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

3. Experience Refinement (Bullet Point Adjustments):
o Modify my previous experience to better match the job description.
o Ensure the changes sound natural and human-like, avoiding exaggeration while enhancing relevance.
o Present each bullet point modification in a structured format:
   Original Bullet
   Modified Bullet
   Reason for Change
✅ Use markdown syntax to format the mismatch table. Do not use bullet points or paragraph explanations.

4. Change Log for Bullet Points:
o Track all modifications made in the experience section.
o Do not change too much—just enough to pass ATS filters while keeping my resume realistic and authentic.

5. Skills Section Enhancement:
o Suggest changes to my skills section by adding, rewording, or adjusting skills to align with the job description.
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

# --- Parse Structured GPT Response ---
def parse_gpt_response(text):
    qualifications = re.findall(r"Qualification:\s*(.*?)\nMatch %:\s*(\d+)%\nMatch:\s*(Yes|No)", text, re.DOTALL)
    if not qualifications:
        return None
    data = [{
        "Qualification": q.strip(),
        "Match %": f"{m.strip()}%",
        "Match": match.strip()
    } for q, m, match in qualifications]
    return pd.DataFrame(data)

# --- UI Layout ---
jd_input = st.text_area("📄 Paste Job Description here")

uploaded_file = st.file_uploader("📎 Upload Your Resume (.docx or .pdf)", type=["pdf", "docx"])

if st.button("🔍 Analyze Resume"):
    if not uploaded_file or not jd_input.strip():
        st.warning("Please upload a resume and paste the job description.")
    else:
        with st.spinner("Analyzing... this may take a few seconds..."):
            if uploaded_file.name.endswith(".pdf"):
                resume_text = extract_text_from_pdf(uploaded_file)
            else:
                resume_text = extract_text_from_docx(uploaded_file)

            result = get_ats_score(resume_text, jd_input)
            st.success("✅ Analysis Complete!")

            st.markdown("### 📊 Mismatch Analysis Table")
            df = parse_gpt_response(result)
            if df is not None:
                st.dataframe(df)
            else:
                st.info("⚠️ GPT response could not be parsed into a table.")

            st.markdown("### 📝 Full GPT Response")
            st.markdown(result)
