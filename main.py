import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTML_Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from fpdf import FPDF

# Initialize FastAPI
app = FastAPI()

# Enable CORS for Cloud Deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

class CodeRequest(BaseModel):
    code: str
    language: str

class PDFRequest(BaseModel):
    feedback: str
    language: str

# --- FRONTEND HTML CONTENT ---
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Code Lab Pro | Smart Reviewer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: radial-gradient(circle at top right, #111827, #000000); font-family: 'Inter', sans-serif; }
        .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .loader { border-top-color: #3b82f6; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="text-white min-h-screen p-4 md:p-10">
    <div class="max-w-6xl mx-auto">
        <header class="text-center mb-10">
            <h1 class="text-4xl md:text-6xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500 mb-2">AI Code Lab Pro</h1>
            <p class="text-gray-400">Professional Logic & Complexity Analysis</p>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="glass p-6 rounded-3xl shadow-2xl">
                <div class="flex justify-between mb-4">
                    <select id="language" class="bg-gray-800 text-sm px-3 py-2 rounded-lg outline-none border border-gray-700">
                        <option value="C++">C++</option>
                        <option value="Python">Python</option>
                        <option value="Java">Java</option>
                    </select>
                    <span class="text-xs text-gray-500 font-mono self-center">SOURCE_CODE</span>
                </div>
                <textarea id="codeInput" class="w-full h-[400px] bg-black/50 text-blue-300 p-5 rounded-2xl font-mono text-sm border border-gray-800 focus:border-blue-500 outline-none transition-all resize-none" placeholder="// Paste your code here..."></textarea>
                <button onclick="runAnalysis()" id="runBtn" class="w-full mt-6 bg-blue-600 hover:bg-blue-500 py-4 rounded-2xl font-bold text-lg transition-transform active:scale-95 shadow-lg shadow-blue-500/20">Analyze Logic</button>
            </div>

            <div class="flex flex-col">
                <div id="placeholder" class="glass h-full rounded-3xl flex items-center justify-center border-dashed border-2 border-gray-700 opacity-50">
                    <p class="text-gray-500 text-center">Results will appear here<br>after analysis.</p>
                </div>

                <div id="resultCard" class="hidden glass h-full rounded-3xl p-6 flex flex-col border-t-4 border-blue-500">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="font-bold text-blue-400 flex items-center gap-2"><span>⚡</span> Analysis Report</h3>
                        <button onclick="downloadPDF()" class="bg-green-600/20 hover:bg-green-600/40 text-green-400 text-xs font-bold px-4 py-2 rounded-lg border border-green-500/30 transition-all">
                            📥 EXPORT PDF
                        </button>
                    </div>
                    <div id="resultText" class="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap overflow-y-auto max-h-[450px]"></div>
                </div>
            </div>
        </div>
    </div>

    <div id="loader" class="hidden fixed inset-0 bg-black/90 z-50 flex flex-col items-center justify-center">
        <div class="loader ease-linear rounded-full border-4 border-t-4 border-gray-700 h-16 w-16 mb-4"></div>
        <p class="text-blue-400 font-bold animate-pulse text-xl">Gemini is Reviewing Logic...</p>
    </div>

    <script>
        async function runAnalysis() {
            const code = document.getElementById('codeInput').value;
            const lang = document.getElementById('language').value;
            if(!code.trim()) return alert("Please enter code!");

            document.getElementById('loader').classList.remove('hidden');

            try {
                const res = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ code, language: lang })
                });
                const data = await res.json();

                document.getElementById('placeholder').classList.add('hidden');
                document.getElementById('resultCard').classList.remove('hidden');
                document.getElementById('resultText').innerText = data.analysis;
            } catch (e) {
                alert("Error connecting to server.");
            } finally {
                document.getElementById('loader').classList.add('hidden');
            }
        }

        async function downloadPDF() {
            const feedback = document.getElementById('resultText').innerText;
            const language = document.getElementById('language').value;

            const res = await fetch('/api/download', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ feedback, language })
            });

            if(res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Code_Review_${language}.pdf`;
                a.click();
            }
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get_index():
    return HTMLResponse(content=html_content)

@app.post("/analyze")
async def analyze_code(req: CodeRequest):
    prompt = f"Act as a Senior Software Engineer. Analyze this {req.language} code for logic errors, efficiency, and time complexity. Suggest improvements:\\n\\n{req.code}"
    response = model.generate_content(prompt)
    return {"analysis": response.text}

@app.post("/api/download")
async def download_pdf(req: PDFRequest):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, f"Technical Code Review - {req.language}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 10, req.feedback)

    pdf_bytes = pdf.output(dest='S')
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=review.pdf"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)