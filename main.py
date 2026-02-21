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
        headers={"Content-Disposition": "attachment; filename=CodeReview.pdf"})


# 2. Robust Frontend
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Code Lab Pro | Smart Reviewer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: radial-gradient(circle at top right, #1a1c2c, #0d0e14); }
        .code-font { font-family: 'Fira Code', monospace; }
        .glass-card { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .gradient-text { background: linear-gradient(90deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .loader { border-top-color: #60a5fa; animation: spinner 1.5s linear infinite; }
        @keyframes spinner { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="text-gray-200 min-h-screen">
    <div class="max-w-6xl mx-auto px-4 py-12">
        <header class="text-center mb-12">
            <h1 class="text-5xl font-extrabold mb-4 gradient-text">AI Code Lab Pro</h1>
            <p class="text-gray-400 text-lg">Your Intelligent C++, Python, and Java Senior Engineer</p>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="glass-card p-6 rounded-2xl shadow-2xl">
                <div class="flex justify-between items-center mb-4">
                    <select id="language-select" class="bg-gray-800 text-sm font-semibold p-2 rounded-lg border border-gray-700 outline-none focus:border-blue-500">
                        <option value="C++">C++</option>
                        <option value="Python">Python</option>
                        <option value="Java">Java</option>
                    </select>
                    <span class="text-xs text-gray-500 font-mono uppercase tracking-widest">Input Editor</span>
                </div>
                <textarea id="code-input" spellcheck="false" class="w-full h-96 bg-[#090a0f] text-blue-300 p-4 rounded-xl code-font text-sm border border-gray-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all resize-none" placeholder="// Paste your code here to begin analysis..."></textarea>
                <button onclick="analyzeCode()" id="analyze-btn" class="mt-6 w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl transition-all transform hover:scale-[1.01] active:scale-[0.98] shadow-lg shadow-blue-900/20">
                    Run Smart Analysis
                </button>
            </div>

            <div class="flex flex-col gap-6">
                <div id="result-placeholder" class="glass-card h-full rounded-2xl p-8 flex flex-center items-center justify-center text-center border-dashed border-2 border-gray-700">
                    <div>
                        <div class="text-4xl mb-4">🤖</div>
                        <p class="text-gray-500">Submit code to see the AI's <br>logic and complexity report.</p>
                    </div>
                </div>

                <div id="result-card" class="hidden glass-card p-6 rounded-2xl shadow-2xl h-full border-t-4 border-t-blue-500">
                    <div class="flex justify-between items-center mb-6">
                        <h3 class="font-bold text-xl text-blue-400 flex items-center gap-2">
                            <span>✨</span> Analysis Report
                        </h3>
                        <button onclick="downloadPDF()" class="bg-gray-800 hover:bg-gray-700 text-xs text-green-400 font-bold px-4 py-2 rounded-lg border border-green-900/30 flex items-center gap-2 transition-all">
                            📥 EXPORT PDF
                        </button>
                    </div>
                    <div id="result-content" class="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap overflow-y-auto max-h-[450px] pr-2"></div>
                </div>
            </div>
        </div>
    </div>

    <div id="loading-overlay" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div class="flex flex-col items-center">
            <div class="loader ease-linear rounded-full border-4 border-t-4 border-gray-200 h-12 w-12 mb-4"></div>
            <h2 class="text-center text-white text-xl font-semibold">Gemini is Thinking...</h2>
            <p class="w-1/3 text-center text-gray-400">Reviewing logic, complexity, and best practices.</p>
        </div>
    </div>

    <script>
        async function analyzeCode() {
            const code = document.getElementById('code-input').value;
            const lang = document.getElementById('language-select').value;
            const overlay = document.getElementById('loading-overlay');
            const placeholder = document.getElementById('result-placeholder');
            const resultCard = document.getElementById('result-card');
            const resultContent = document.getElementById('result-content');

            if (!code.trim()) return alert("Please paste some code first!");

            overlay.classList.remove('hidden');

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ code: code, language: lang })
                });

                const data = await response.json();

                placeholder.classList.add('hidden');
                resultCard.classList.remove('hidden');
                resultContent.innerText = data.analysis;
            } catch (error) {
                alert("Connection failed. Check your API key!");
            } finally {
                overlay.classList.add('hidden');
            }
        }

        async function downloadPDF() {
            const feedback = document.getElementById('result-content').innerText;
            const language = document.getElementById('language-select').value;

            try {
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
                    a.download = `RGUKT_CodeReview_${language}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                } else {
                    alert("Error creating PDF. Make sure fpdf2 is installed.");
                }
            } catch (err) {
                alert("Request failed. Check your internet.");
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
