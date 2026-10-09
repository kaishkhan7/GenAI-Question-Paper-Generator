
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pathlib import Path
import os
import io
import re
from datetime import date

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="GenAI Question Paper Generator",
    page_icon="📝",
    layout="centered"
)

# =====================================================
# API CONFIG
# =====================================================

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEY not found in .env file.")
    st.stop()

client = OpenAI(api_key=api_key)

# =====================================================
# PDF GENERATOR
# =====================================================

def create_pdf(
    text,
    subject,
    course,
    semester,
    exam_type,
    exam_date,
    duration,
    total_marks,
    document_title="QUESTION PAPER"
):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    y = height - 30

    # Default COER logo
    logo_path = Path(__file__).resolve().parent / "COER-University-Logo.png"

    if logo_path.exists():
        try:
            logo = ImageReader(str(logo_path))
            logo_width = 390
            logo_height = 135

            pdf.drawImage(
                logo,
                (width - logo_width) / 2,
                y - logo_height,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto"
            )
            y -= 145
        except Exception:
            pass

    # University heading
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, y, "COER UNIVERSITY")
    y -= 23

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(width / 2, y, course[:70])
    y -= 20

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(width / 2, y, document_title)
    y -= 18

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        width / 2,
        y,
        f"{semester} | {exam_type}"
    )
    y -= 18

    pdf.line(40, y, width - 40, y)
    y -= 25

    # Exam details box
    pdf.setLineWidth(1)
    pdf.roundRect(45, y - 55, width - 90, 55, 6)

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(55, y - 18, f"Subject: {subject[:40]}")
    pdf.drawRightString(
        width - 55,
        y - 18,
        f"Date: {exam_date}"
    )
    pdf.drawString(55, y - 40, f"Time: {duration} Minutes")
    pdf.drawRightString(
        width - 55,
        y - 40,
        f"Maximum Marks: {total_marks}"
    )

    y -= 75

    # Blank student details for pen
    pdf.roundRect(45, y - 75, width - 90, 75, 6)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(55, y - 17, "Student Details")

    pdf.setFont("Helvetica", 9)
    pdf.drawString(55, y - 38, "Student Name:")
    pdf.line(125, y - 40, 285, y - 40)

    pdf.drawString(315, y - 38, "Roll No.:")
    pdf.line(365, y - 40, width - 55, y - 40)

    pdf.drawString(55, y - 60, "Enrollment No.:")
    pdf.line(140, y - 62, 300, y - 62)

    pdf.drawString(330, y - 60, "Class / Section:")
    pdf.line(415, y - 62, width - 55, y - 62)

    y -= 95

    # Instructions
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Instructions:")
    y -= 17

    instructions = [
        "1. Read each question carefully.",
        "2. Marks are indicated against each question.",
        "3. Follow the attempt instructions for each section.",
        "4. Answer according to the given instructions."
    ]

    pdf.setFont("Helvetica", 9)

    for instruction in instructions:
        if y < 60:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 9)

        pdf.drawString(60, y, instruction)
        y -= 14

    y -= 10
    pdf.line(50, y, width - 50, y)
    y -= 22

    # Render question paper content
    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            y -= 7
            continue

        # Remove basic Markdown heading/bold markers
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = line.replace("**", "").replace("__", "")
        line = line.replace("`", "")

        if y < 55:
            pdf.showPage()
            y = height - 50

        # Box section headings
        if (
            line.upper().startswith("SECTION")
            or line.upper().startswith("PART")
        ):
            if y < 80:
                pdf.showPage()
                y = height - 50

            pdf.roundRect(
                45,
                y - 20,
                width - 90,
                25,
                5
            )
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawCentredString(width / 2, y - 12, line[:85])
            y -= 32
            pdf.setFont("Helvetica", 10)
            continue

        # Wrap text to fit page width
        words = line.split()
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()

            if pdf.stringWidth(test_line, "Helvetica", 10) > width - 100:
                if current_line:
                    if y < 45:
                        pdf.showPage()
                        y = height - 50
                        pdf.setFont("Helvetica", 10)

                    pdf.drawString(50, y, current_line)
                    y -= 15

                current_line = word
            else:
                current_line = test_line

        if current_line:
            if y < 45:
                pdf.showPage()
                y = height - 50

            pdf.setFont("Helvetica", 10)
            pdf.drawString(50, y, current_line)
            y -= 15

    # Footer on the final page
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(
        width / 2,
        25,
        "COER University | GenAI Question Paper Generator | Created by Kaish Khan"
    )

    pdf.save()
    buffer.seek(0)
    return buffer

# =====================================================
# APP STYLING
# =====================================================

st.markdown(
    """
    <style>
    .main {
        background-color: #f5f7fb;
    }
    h1 {
        text-align: center;
    }
    .stButton > button,
    .stDownloadButton > button {
        width: 100%;
        border-radius: 10px;
        min-height: 3em;
        font-size: 16px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# TITLE AND DEVELOPER CREDIT
# =====================================================

st.title("📝 GenAI Question Paper Generator")

st.write(
    "Generate a professional college-level question paper using Generative AI."
)

st.markdown(
    """
    <div style="text-align:center; color:gray;">
        Developed by <b>Kaish Khan</b>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

st.subheader("🏫 University Details")
st.info(
    "COER University logo is automatically included in PDFs "
    "when COER-University-Logo.png is in the app folder."
)

# =====================================================
# EXAMINATION DETAILS
# =====================================================

st.subheader("📋 Examination Details")

subject = st.text_input(
    "📚 Subject Name",
    placeholder="Example: C++"
)

course = st.text_input(
    "🎓 Course / Program",
    placeholder="Example: B.Tech CSE AI & ML"
)

semester = st.selectbox(
    "📖 Semester",
    [
        "1st Semester",
        "2nd Semester",
        "3rd Semester",
        "4th Semester",
        "5th Semester",
        "6th Semester",
        "7th Semester",
        "8th Semester"
    ]
)

exam_type = st.selectbox(
    "📝 Examination Type",
    [
        "Internal Assessment",
        "Mid Semester Examination",
        "End Semester Examination",
        "Practice Examination"
    ]
)

exam_date = st.date_input("📅 Exam Date", value=date.today())

topics = st.text_area(
    "📖 Units / Topics",
    placeholder="Example: Functions, Classes, Objects, Operators"
)

difficulty = st.selectbox(
    "🎯 Difficulty Level",
    ["Easy", "Medium", "Hard", "Mixed"]
)

st.subheader("👤 Student Details")
st.info(
    "Student details will remain blank in the PDF so students "
    "can fill them in by pen."
)

# =====================================================
# QUESTION PAPER PATTERN
# =====================================================

question_type = st.selectbox(
    "📝 Question Paper Pattern",
    [
        "MCQ Only",
        "Short Answer Only",
        "Long Answer Only",
        "Mixed (MCQ + Short + Long)"
    ]
)

st.subheader("📊 Question & Marks Distribution")

# Defaults for unused sections
mcq_questions = 0
mcq_marks = 0
mcq_attempt = 0
mcq_attempt_type = "Attempt All"
mcq_total = 0

short_questions = 0
short_marks = 0
short_attempt = 0
short_attempt_type = "Attempt All"
short_total = 0

long_questions = 0
long_marks = 0
long_attempt = 0
long_attempt_type = "Attempt All"
long_total = 0

# =====================================================
# MCQ ONLY
# =====================================================

if question_type == "MCQ Only":
    mcq_questions = st.number_input(
        "🔵 Number of MCQs to Generate",
        min_value=1,
        max_value=30,
        value=10,
        key="mcq_only_questions"
    )

    mcq_attempt_type = st.selectbox(
        "📝 MCQ Attempt Rule",
        ["Attempt All", "Attempt Any N"],
        key="mcq_attempt_type"
    )

    if mcq_attempt_type == "Attempt Any N":
        mcq_attempt = st.number_input(
            "✏️ Attempt Any How Many?",
            min_value=1,
            max_value=int(mcq_questions),
            value=min(5, int(mcq_questions)),
            key="mcq_attempt"
        )
    else:
        mcq_attempt = int(mcq_questions)

    mcq_marks = st.number_input(
        "⭐ Marks per MCQ",
        min_value=1,
        max_value=20,
        value=1,
        key="mcq_only_marks"
    )

    total_questions = int(mcq_questions)
    total_attempted = int(mcq_attempt)
    total_marks = int(mcq_attempt * mcq_marks)

# =====================================================
# SHORT ANSWER ONLY
# =====================================================

elif question_type == "Short Answer Only":
    short_questions = st.number_input(
        "🟢 Number of Short Questions to Generate",
        min_value=1,
        max_value=30,
        value=5,
        key="short_only_questions"
    )

    short_attempt_type = st.selectbox(
        "📝 Short Question Attempt Rule",
        ["Attempt All", "Attempt Any N"],
        key="short_attempt_type"
    )

    if short_attempt_type == "Attempt Any N":
        short_attempt = st.number_input(
            "✏️ Attempt Any How Many?",
            min_value=1,
            max_value=int(short_questions),
            value=min(3, int(short_questions)),
            key="short_attempt"
        )
    else:
        short_attempt = int(short_questions)

    short_marks = st.number_input(
        "⭐ Marks per Short Question",
        min_value=1,
        max_value=20,
        value=3,
        key="short_only_marks"
    )

    total_questions = int(short_questions)
    total_attempted = int(short_attempt)
    total_marks = int(short_attempt * short_marks)

# =====================================================
# LONG ANSWER ONLY
# =====================================================

elif question_type == "Long Answer Only":
    long_questions = st.number_input(
        "🟠 Number of Long Questions to Generate",
        min_value=1,
        max_value=30,
        value=4,
        key="long_only_questions"
    )

    long_attempt_type = st.selectbox(
        "📝 Long Question Attempt Rule",
        ["Attempt All", "Attempt Any N"],
        key="long_attempt_type"
    )

    if long_attempt_type == "Attempt Any N":
        long_attempt = st.number_input(
            "✏️ Attempt Any How Many?",
            min_value=1,
            max_value=int(long_questions),
            value=min(2, int(long_questions)),
            key="long_attempt"
        )
    else:
        long_attempt = int(long_questions)

    long_marks = st.number_input(
        "⭐ Marks per Long Question",
        min_value=1,
        max_value=20,
        value=5,
        key="long_only_marks"
    )

    total_questions = int(long_questions)
    total_attempted = int(long_attempt)
    total_marks = int(long_attempt * long_marks)

# =====================================================
# MIXED PAPER
# =====================================================

else:
    st.markdown("### 🔵 Section A — MCQ")

    mcq_questions = st.number_input(
        "Number of MCQs to Generate",
        min_value=1,
        max_value=20,
        value=8,
        key="mixed_mcq_questions"
    )

    mcq_attempt_type = st.selectbox(
        "MCQ Attempt Rule",
        ["Attempt All", "Attempt Any N"],
        key="mixed_mcq_attempt_type"
    )

    if mcq_attempt_type == "Attempt Any N":
        mcq_attempt = st.number_input(
            "Attempt Any How Many MCQs?",
            min_value=1,
            max_value=int(mcq_questions),
            value=min(5, int(mcq_questions)),
            key="mixed_mcq_attempt"
        )
    else:
        mcq_attempt = int(mcq_questions)

    mcq_marks = st.number_input(
        "Marks per MCQ",
        min_value=1,
        max_value=20,
        value=1,
        key="mixed_mcq_marks"
    )

    mcq_total = int(mcq_attempt * mcq_marks)

    st.markdown("### 🟢 Section B — Short Answer")

    short_questions = st.number_input(
        "Number of Short Questions to Generate",
        min_value=1,
        max_value=20,
        value=5,
        key="mixed_short_questions"
    )

    short_attempt_type = st.selectbox(
        "Short Question Attempt Rule",
        ["Attempt All", "Attempt Any N"],
        key="mixed_short_attempt_type"
    )

    if short_attempt_type == "Attempt Any N":
        short_attempt = st.number_input(
            "Attempt Any How Many Short Questions?",
            min_value=1,
            max_value=int(short_questions),
            value=min(3, int(short_questions)),
            key="mixed_short_attempt"
        )
    else:
        short_attempt = int(short_questions)

    short_marks = st.number_input(
        "Marks per Short Question",
        min_value=1,
        max_value=20,
        value=2,
        key="mixed_short_marks"
    )

    short_total = int(short_attempt * short_marks)

    st.markdown("### 🟠 Section C — Long Answer")

    long_questions = st.number_input(
        "Number of Long Questions to Generate",
        min_value=1,
        max_value=20,
        value=4,
        key="mixed_long_questions"
    )

    long_attempt_type = st.selectbox(
        "Long Question Attempt Rule",
        ["Attempt All", "Attempt Any N"],
        key="mixed_long_attempt_type"
    )

    if long_attempt_type == "Attempt Any N":
        long_attempt = st.number_input(
            "Attempt Any How Many Long Questions?",
            min_value=1,
            max_value=int(long_questions),
            value=min(2, int(long_questions)),
            key="mixed_long_attempt"
        )
    else:
        long_attempt = int(long_questions)

    long_marks = st.number_input(
        "Marks per Long Question",
        min_value=1,
        max_value=20,
        value=5,
        key="mixed_long_marks"
    )

    long_total = int(long_attempt * long_marks)

    total_questions = int(
        mcq_questions + short_questions + long_questions
    )

    total_attempted = int(
        mcq_attempt + short_attempt + long_attempt
    )

    total_marks = mcq_total + short_total + long_total

    st.success(
        f"Generated Questions: {total_questions} | "
        f"Questions to Attempt: {total_attempted} | "
        f"Maximum Marks: {total_marks}"
    )

# =====================================================
# DURATION
# =====================================================

duration = st.number_input(
    "⏱️ Exam Duration (minutes)",
    min_value=10,
    max_value=300,
    value=60
)

# =====================================================
# ATTEMPT INSTRUCTIONS
# =====================================================

def make_attempt_rule(rule, count, total):
    if rule == "Attempt Any N":
        return f"Attempt any {count} out of {total} questions."
    return f"Attempt all {total} questions."

if question_type == "MCQ Only":
    attempt_instruction = make_attempt_rule(
        mcq_attempt_type, mcq_attempt, mcq_questions
    )
elif question_type == "Short Answer Only":
    attempt_instruction = make_attempt_rule(
        short_attempt_type, short_attempt, short_questions
    )
elif question_type == "Long Answer Only":
    attempt_instruction = make_attempt_rule(
        long_attempt_type, long_attempt, long_questions
    )
else:
    attempt_instruction = "\n".join([
        "Section A: " + make_attempt_rule(
            mcq_attempt_type, mcq_attempt, mcq_questions
        ),
        "Section B: " + make_attempt_rule(
            short_attempt_type, short_attempt, short_questions
        ),
        "Section C: " + make_attempt_rule(
            long_attempt_type, long_attempt, long_questions
        )
    ])

# =====================================================
# AI PROMPT
# =====================================================

if question_type == "MCQ Only":
    section_instruction = f"""
Generate exactly {mcq_questions} MCQs.
Attempt rule: {attempt_instruction}
Each MCQ carries {mcq_marks} mark.
Maximum marks: {total_marks}
"""
elif question_type == "Short Answer Only":
    section_instruction = f"""
Generate exactly {short_questions} short-answer questions.
Attempt rule: {attempt_instruction}
Each question carries {short_marks} marks.
Maximum marks: {total_marks}
"""
elif question_type == "Long Answer Only":
    section_instruction = f"""
Generate exactly {long_questions} long-answer questions.
Attempt rule: {attempt_instruction}
Each question carries {long_marks} marks.
Maximum marks: {total_marks}
"""
else:
    section_instruction = f"""
SECTION A - MCQ
Generate exactly {mcq_questions} MCQs.
Attempt rule: {make_attempt_rule(mcq_attempt_type, mcq_attempt, mcq_questions)}
Each MCQ carries {mcq_marks} mark.
Section maximum marks: {mcq_total}

SECTION B - SHORT ANSWER
Generate exactly {short_questions} short-answer questions.
Attempt rule: {make_attempt_rule(short_attempt_type, short_attempt, short_questions)}
Each question carries {short_marks} marks.
Section maximum marks: {short_total}

SECTION C - LONG ANSWER
Generate exactly {long_questions} long-answer questions.
Attempt rule: {make_attempt_rule(long_attempt_type, long_attempt, long_questions)}
Each question carries {long_marks} marks.
Section maximum marks: {long_total}

Total generated questions: {total_questions}
Total questions to attempt: {total_attempted}
Maximum marks: {total_marks}
"""

prompt = f"""
Create a professional college-level question paper.

Subject: {subject}
Course / Program: {course}
Semester: {semester}
Examination Type: {exam_type}
Exam Date: {exam_date}
Topics: {topics}
Difficulty Level: {difficulty}
Question Paper Pattern: {question_type}
Duration: {duration} minutes.

{section_instruction}

Requirements:
1. Generate exactly the requested number of questions.
2. Do not generate fewer or extra questions.
3. Base questions only on the provided topics.
4. Follow the selected difficulty level.
5. Avoid duplicate questions.
6. Number questions clearly and mention marks.
7. Follow all attempt rules and marks exactly.
8. Do not provide answers in the question paper.
9. Maximum marks must be based on the questions students must attempt.

MCQ requirements:
- Give exactly four options: A, B, C and D.
- Do not reveal the correct answer.

Short-answer requirements:
- Create meaningful questions requiring concise explanations.

Long-answer requirements:
- Create descriptive questions requiring detailed answers.

Mixed requirements:
- Clearly label Section A, Section B and Section C.
- Follow each section's question count, attempt rule and marks.
"""

# =====================================================
# GENERATE QUESTION PAPER
# =====================================================

if st.button(
    "🚀 Generate Question Paper",
    use_container_width=True
):
    if not subject.strip() or not topics.strip():
        st.warning("Please enter the subject and topics.")
        st.stop()

    try:
        with st.spinner("🤖 AI is generating your question paper..."):
            response = client.responses.create(
                model="gpt-6-luna",
                input=prompt
            )

        st.session_state["question_paper"] = response.output_text
        st.session_state.pop("answer_key", None)
        st.success("Question paper generated successfully!")

    except Exception as e:
        st.error("Something went wrong while generating the paper.")
        st.code(str(e))

# =====================================================
# DISPLAY QUESTION PAPER AND PDF
# =====================================================

if "question_paper" in st.session_state:
    question_paper = st.session_state["question_paper"]

    st.divider()
    st.markdown(f"""
# 🏫 COER UNIVERSITY

### {course}
### {exam_type}

**Subject:** {subject}

**Semester:** {semester}

**Exam Date:** {exam_date}

**Time:** {duration} Minutes

**Maximum Marks:** {total_marks}

---

### 👤 Student Details

**Student Name:** ________________________________

**Roll Number:** _________________________________

**Enrollment Number:** ___________________________

**Class / Section:** ______________________________

---

### 📌 Instructions

1. Read each question carefully.
2. Marks are indicated against each question.
3. Follow the attempt instructions for each section.
4. Answer according to the instructions.

### 📝 Attempt Instructions

{attempt_instruction}

---
""")

    st.markdown(question_paper)

    pdf_file = create_pdf(
        question_paper,
        subject,
        course,
        semester,
        exam_type,
        str(exam_date),
        duration,
        total_marks,
        "QUESTION PAPER"
    )

    st.download_button(
        label="📥 Download Question Paper PDF",
        data=pdf_file,
        file_name=f"{subject}_Question_Paper.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    st.divider()

    # =================================================
    # GENERATE ANSWER KEY
    # =================================================

    if st.button(
        "🔑 Generate Answer Key",
        use_container_width=True
    ):
        answer_prompt = f"""
Create a professional answer key for this question paper.

Subject: {subject}

Question Paper:
{question_paper}

Requirements:
1. Provide answers for ALL generated questions.
2. For MCQs, provide the correct option and answer.
3. For short-answer questions, give concise correct answers.
4. For long-answer questions, provide important key points.
5. Keep the original question numbering.
6. Do not create new questions.
7. Include questions students may choose not to attempt.
"""

        try:
            with st.spinner("🔑 AI is generating the answer key..."):
                answer_response = client.responses.create(
                    model="gpt-6-luna",
                    input=answer_prompt
                )

            st.session_state["answer_key"] = answer_response.output_text
            st.success("Answer key generated successfully!")

        except Exception as e:
            st.error("Could not generate the answer key.")
            st.code(str(e))

# =====================================================
# DISPLAY ANSWER KEY AND PDF
# =====================================================

if "answer_key" in st.session_state:
    st.divider()
    st.markdown("## 🔑 Answer Key")

    answer_key = st.session_state["answer_key"]
    st.markdown(answer_key)

    answer_pdf = create_pdf(
        answer_key,
        subject,
        course,
        semester,
        exam_type,
        str(exam_date),
        duration,
        total_marks,
        "ANSWER KEY"
    )

    st.download_button(
        label="📥 Download Answer Key PDF",
        data=answer_pdf,
        file_name=f"{subject}_Answer_Key.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# =====================================================
# FOOTER
# =====================================================

st.divider()
st.caption("🤖 GenAI Question Paper Generator | Developed by Kaish Khan")
