import fitz  # PyMuPDF for PDFs
from docx import Document
import streamlit as st
from openai import OpenAI

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

# --- Send to GPT for ATS Match Analysis ---
def get_ats_score(resume, jd):
    prompt = f"""
I am applying for a job and want to optimize my resume for better alignment with the job description. Follow these structured steps to analyze, compare, and refine my resume while keeping it natural and ATS-friendly.

1. Extract all Responsibilities & Qualifications:
- Identify and highlight all responsibilities and qualifications from the job description.
- Summarize them concisely.

2. Mismatch Analysis (Tabular Format):
- Compare the resume against qualifications line by line.
- Output a table with:
  - Job Qualification
  - Resume Match % Estimate
  - Match (Yes/No)

3. Experience Refinement:
- Modify my resume bullet points to better match the JD.
- Keep it realistic and human-like.
- Format:
  - Original Bullet
  - Modified Bullet
  - Reason for Change

4. Change Log:
- Track what was modified and why.
- Keep changes minimal yet impactful.

5. Skills Section Enhancement:
- Suggest edits to skills section based on the JD.
- Prioritize industry-relevant keywords.

📌 Important Notes:
- Keep changes subtle and realistic.
- Optimize for ATS without making it unnatural.

Job Description:
{jd}

Resume:
{resume}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # or "gpt-4" if you have access
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    return response.choices[0].message.content

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
            st.markdown("### 📈 GPT Analysis Result")
            st.markdown(result)
