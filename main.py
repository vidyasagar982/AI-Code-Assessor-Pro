import os
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai
from fpdf import FPDF
import uvicorn

# 1. Setup AI Client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

app = FastAPI()


class CodeSubmission(BaseModel):
    code: str
    language: str
    persona: str


@app.post("/api/assess")
async def assess_code(submission: CodeSubmission):
    try:
        role = "Senior Engineer" if submission.persona == "senior" else "Coding Tutor"
        prompt = f"Act as a {role}. Analyze this {submission.language} code for bugs, logic, and complexity. Use Markdown formatting.\n\nCODE:\n{submission.code}"
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite', contents=prompt)
        return {"feedback": response.text}
    except Exception as e:
        return {"feedback": f"**AI Error:** {str(e)}"}


@app.post("/api/download")
async def download_pdf(data: dict):
    feedback = data.get("feedback", "No feedback available.")
    language = data.get("language", "Code")

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, f"AI Code Review Report - {language}", ln=True, align='C')
    pdf.ln(10)

    # Body Content
    pdf.set_font("Helvetica", size=12)
    # multi_cell handles long text and automatic line breaks
    pdf.multi_cell(0, 10, feedback)

    # Output as binary data (this is better for Render/Cloud)
    pdf_bytes = pdf.output(dest='S') 

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=CodeReview.pdf"}
    )


# 2. Robust Frontend
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Code Lab Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold mb-6 text-blue-400">AI Code Lab Pro 🚀</h1>

        <div class="bg-gray-800 p-6 rounded-xl shadow-lg mb-6">
            <select id="language-select" class="bg-gray-700 text-white p-2 rounded mb-4 w-full">
                <option value="C++">C++</option>
                <option value="Python">Python</option>
                <option value="Java">Java</option>
            </select>
            <textarea id="code-input" rows="10" class="w-full bg-gray-900 text-green-400 p-4 rounded-lg font-mono mb-4" placeholder="Paste your code here..."></textarea>
            <button onclick="analyzeCode()" id="analyze-btn" class="bg-blue-600 hover:bg-blue-700 w-full py-3 rounded-lg font-bold transition-all">Analyze Code</button>
        </div>

        <div id="result-section" class="hidden bg-gray-800 p-6 rounded-xl shadow-lg">
            <h2 class="text-xl font-semibold mb-4 text-green-400">Analysis Result:</h2>
            <div id="result-content" class="bg-gray-900 p-4 rounded-lg text-gray-300 whitespace-pre-wrap mb-4"></div>

            <button onclick="downloadPDF()" class="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-bold flex items-center gap-2">
                📥 Download PDF Report
            </button>
        </div>
    </div>

    <script>
        async function analyzeCode() {
            const btn = document.getElementById('analyze-btn');
            const code = document.getElementById('code-input').value;
            const lang = document.getElementById('language-select').value;

            btn.innerText = "Analyzing...";
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ code: code, language: lang })
            });
            const data = await response.json();

            document.getElementById('result-section').classList.remove('hidden');
            document.getElementById('result-content').innerText = data.analysis;
            btn.innerText = "Analyze Code";
        }

        async function downloadPDF() {
            const feedback = document.getElementById('result-content').innerText;
            const language = document.getElementById('language-select').value;

            const response = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ feedback, language })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `CodeReview_${language}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
            } else {
                alert("Error generating PDF. Please try again.");
            }
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return html_content





# ... your existing code ...

if __name__ == "__main__":
    import uvicorn
    # Render provides a PORT environment variable; we default to 10000
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This allows your frontend to talk to the backend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
