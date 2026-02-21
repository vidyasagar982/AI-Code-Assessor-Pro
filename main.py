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
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Code Lab Pro</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>

    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0b0f1a; color: white; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: auto; display: flex; flex-direction: column; gap: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 800px) { .grid { grid-template-columns: 1fr; } }

        .panel { background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; display: flex; flex-direction: column; }
        textarea { width: 100%; height: 300px; background: #020617; color: #38bdf8; border: 1px solid #475569; border-radius: 8px; padding: 10px; font-family: monospace; resize: none; box-sizing: border-box; }

        .results { background: #020617; padding: 15px; border-radius: 8px; min-height: 300px; overflow-y: auto; font-size: 14px; line-height: 1.6; }
        .results h1, .results h2 { color: #38bdf8; }
        .results code { background: #1e293b; padding: 2px 4px; border-radius: 4px; }
        .results pre { background: #1e293b !important; padding: 10px; border-radius: 8px; }

        button { background: #38bdf8; color: #0b0f1a; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        button:disabled { background: #475569; cursor: not-allowed; }
        select { background: #334155; color: white; border: none; padding: 8px; border-radius: 4px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        function App() {
            const [code, setCode] = React.useState("");
            const [lang, setLang] = React.useState("cpp");
            const [persona, setPersona] = React.useState("senior");
            const [feedback, setFeedback] = React.useState("");
            const [loading, setLoading] = React.useState(false);

            const analyze = async () => {
                if(!code) return alert("Please paste some code first!");
                setLoading(true);
                try {
                    const res = await fetch('/api/assess', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({code, language: lang, persona})
                    });
                    const data = await res.json();
                    setFeedback(data.feedback);
                    // Trigger highlighting after a tiny delay to let Markdown render
                    setTimeout(() => Prism.highlightAll(), 100);
                } catch (e) { setFeedback("Error: " + e.message); }
                setLoading(false);
            };

            return (
                <div className="container">
                    <header style={{textAlign:'center'}}>
                        <h1>🧠 AI Code Lab Pro</h1>
                    </header>
                    <div className="grid">
                        <div className="panel">
                            <div style={{display:'flex', justifyContent:'space-between'}}>
                                <select value={lang} onChange={e => setLang(e.target.value)}>
                                    <option value="cpp">C++</option>
                                    <option value="python">Python</option>
                                    <option value="java">Java</option>
                                </select>
                                <select value={persona} onChange={e => setPersona(e.target.value)}>
                                    <option value="senior">Senior Engineer</option>
                                    <option value="tutor">Coding Tutor</option>
                                </select>
                            </div>
                            <textarea value={code} onChange={e => setCode(e.target.value)} placeholder="// Paste your code here..." />
                            <button onClick={analyze} disabled={loading}>{loading ? "Analyzing..." : "Analyze Code"}</button>
                        </div>
                        <div className="panel">
                            <h3>Assessment Report</h3>
                            <div className="results" dangerouslySetInnerHTML={{ __html: feedback ? marked.parse(feedback) : "Analysis will appear here..." }} />
                        </div>
                    </div>
                </div>
            );
        }
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
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
