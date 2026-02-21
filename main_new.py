import os
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai
from fpdf import FPDF
from fastapi.middleware.cors import CORSMiddleware

# 1. Setup AI Client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

app = FastAPI()

# --- MIDDLEWARE MUST BE ADDED BEFORE THE SERVER STARTS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodeSubmission(BaseModel):
    code: str
    language: str
    persona: str


@app.post("/api/assess")
async def assess_code(submission: CodeSubmission):
    try:
        role = "Senior Engineer" if submission.persona == "senior" else "Coding Tutor"
        prompt = f"Act as a {role}. Analyze this {submission.language} code for bugs, logic, and complexity. Use Markdown formatting.\n\nCODE:\n{submission.code}"

        # Ensure model name is correct for your SDK version
        response = client.models.generate_content(model='gemini-2.0-flash',
                                                  contents=prompt)
        return {"feedback": response.text}
    except Exception as e:
        return {"feedback": f"**AI Error:** {str(e)}"}


@app.post("/api/download")
async def download_pdf(data: dict):
    feedback = data.get("feedback", "No feedback available.")
    language = data.get("language", "Code")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, f"AI Code Review Report - {language}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, feedback)

    pdf_bytes = pdf.output(dest='S')
    return Response(content=pdf_bytes,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition":
                        f"attachment; filename=CodeReview_{language}.pdf"
                    })


# 2. Frontend (Fixed Fetch URL and Payload)
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Code Lab Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #0d0e14; color: #e5e7eb; font-family: sans-serif; }
        .glass-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); }
    </style>
</head>
<body class="p-12">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-4xl font-bold mb-8 text-blue-400">AI Code Lab Pro</h1>
        <div class="grid gap-6">
            <select id="language-select" class="bg-gray-800 p-2 rounded">
                <option value="Python">Python</option>
                <option value="C++">C++</option>
                <option value="Java">Java</option>
            </select>
            <textarea id="code-input" class="w-full h-64 bg-black p-4 text-green-400 font-mono" placeholder="Paste code..."></textarea>
            <button onclick="analyzeCode()" id="btn" class="bg-blue-600 py-3 rounded font-bold">Analyze Code</button>

            <div id="result-card" class="hidden glass-card p-6 rounded-xl mt-4">
                <div class="flex justify-between mb-4">
                    <h2 class="text-xl font-bold">Feedback</h2>
                    <button onclick="downloadPDF()" class="text-green-400 border border-green-400 px-2 rounded">PDF</button>
                </div>
                <div id="result-content" class="whitespace-pre-wrap"></div>
            </div>
        </div>
    </div>

    <script>
        async function analyzeCode() {
            const code = document.getElementById('code-input').value;
            const lang = document.getElementById('language-select').value;
            const btn = document.getElementById('btn');

            if(!code) return alert("Empty code!");
            btn.innerText = "Thinking...";

            try {
                // FIXED: URL matches @app.post("/api/assess")
                const response = await fetch('/api/assess', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    // FIXED: Added persona field required by Pydantic model
                    body: JSON.stringify({ code, language: lang, persona: "senior" })
                });
                const data = await response.json();
                document.getElementById('result-card').classList.remove('hidden');
                document.getElementById('result-content').innerText = data.feedback;
            } catch (e) {
                alert("Error connecting to server");
            } finally {
                btn.innerText = "Analyze Code";
            }
        }

        async function downloadPDF() {
            const feedback = document.getElementById('result-content').innerText;
            const language = document.getElementById('language-select').value;
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ feedback, language })
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = "Report.pdf";
            a.click();
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return html_content


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    # Standard practice: run uvicorn at the very end
    uvicorn.run(app, host="0.0.0.0", port=port)
