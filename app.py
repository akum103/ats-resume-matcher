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
I am applying for a job and want to optimize my resume for better alignment with the job description. Follow these structured steps carefully to analyze, compare, and refine my resume, keeping it natural, human-like, and ATS-friendly. Your output should be clean, concise, and strictly in markdown table format for all relevant sections.

---

### 1. Extract Responsibilities & Qualifications  
- Identify **all core responsibilities and qualifications** from the job description.  
- Distinguish between **Required** and **Preferred** or "Nice to Have" qualifications.  
- Present both categories in **separate markdown tables** with two columns:  
  - Column 1: Category (Responsibility or Qualification)  
  - Column 2: Extracted Text

---

### 2. Mismatch Analysis (Tabular Format)  
- Compare my resume line-by-line with the **job qualifications** (from Required and Preferred).  
- Use **my work experience section and skills section** to find matches.  
- Use this scoring rule:  
  - 80–100% = Clearly mentioned or strongly implied  
  - 50–79% = Partially related or indirectly referenced  
  - <50% = Missing or unclear  

- Present the output in a **markdown table** with these columns:  
  - Column 1: Job Qualification  
  - Column 2: Resume Match % Estimate  
  - Column 3: Match (🟢 Yes / 🟡 Partial / 🔴 No)

✅ Use **markdown table syntax only**. Do not include any extra text before or after the table.

🎯 At the end of this section, give an **Approximate ATS Match Score** (0–100%) based on overall alignment with the job.

---

### 3. Experience Refinement (Bullet Point Adjustments)  
- Only use my **work experience section** for this task.  
- For each company, review all bullets. Modify bullets to better reflect the job description without overexaggerating.  
- If multiple bullets in the same job need changes, include all of them.  
- Preserve authenticity while improving ATS friendliness.  

🧾 Present your suggestions in a **markdown table** with these columns:  
  - Column 1: Company Name  
  - Column 2: Original Bullet  
  - Column 3: Modified Bullet  
  - Column 4: Reason for Change

✅ Do not use bullet points or explanations outside the table.

---

### 4. Change Log for Bullet Points  
- Track **only those bullets that were actually modified** in the Experience Refinement section.  
- Skip any bullets that remained unchanged.  
- Present them clearly and concisely.

✅ Format this as a **markdown table** with 3 columns:  
  - Company Name  
  - What Was Changed  
  - Why


---

### 5. Skills Section Enhancement  
- Analyze my current skills section.  
- Suggest additions, adjustments, or removals based on the job description.  
- Focus on tools, platforms, certifications, and relevant buzzwords.  
- Prioritize industry keywords and CRM/digital/data stack tools if applicable.
- Include tools/platforms like "Microsoft Dynamics, Power Platform, Salesforce" explicitly if mentioned in the JD.
- If a preferred/bonus skill is not harmful, **retain it** rather than remove it.

✅ Present this in a **markdown table** with 3 columns:  
  - Existing Skill  
  - Suggested Action (Keep, Remove, Replace, Add)  
  - Reason / JD Relevance

---

📌 Important Guidelines:  
• Use markdown tables only for structured data.  
• Maintain a human, natural tone in refinements.  
• Keep suggestions ATS-friendly and realistic.  
• DO NOT include introductory text before tables.  
• Make output clean and professional-looking.

---

Now, analyze and refine the resume below using the job description provided.


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
            # Try to extract ATS score (e.g., "ATS Score: 77%")
            match = re.search(r"ATS Score[:\-]?\s*(\d{1,3})%", result)
            ats_score = int(match.group(1)) if match else None
            if ats_score:
                st.markdown("### 🎯 ATS Match Score")
                st.metric(label="📊 ATS Score", value=f"{ats_score}%", delta=None)

                st.progress(ats_score / 100)

                # Emoji-based fit label
                if ats_score >= 85:
                    st.success("🔥 Excellent Fit")
                elif ats_score >= 70:
                    st.info("✅ Good Fit")
                elif ats_score >= 50:
                    st.warning("✍️ Fair Fit — Some Refinement Needed")
                else:
                    st.error("🚧 Weak Fit — Consider Major Edits")

            st.success("✅ Analysis Complete!")

            st.markdown("### 📝 Full GPT Response")
            st.markdown(result)
