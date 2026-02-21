import os
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from fpdf import FPDF

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
# Using the updated model to prevent the grpc_status:5 error
model = genai.GenerativeModel('gemini-2.5-flash')

class CodeRequest(BaseModel):
    code: str
    language: str
    persona: str

class PDFRequest(BaseModel):
    feedback: str
    language: str

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Code Lab Pro</title>

    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>

    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>

    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border: #30363d;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
            --accent: #58a6ff;
            --accent-hover: #3182ce;
            --success: #238636;
            --success-hover: #2ea043;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; background-color: var(--bg-color); color: var(--text-main); line-height: 1.5; padding: 2rem; }

        .container { max-w: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 2rem; }
        .header { text-align: center; margin-bottom: 1rem; }
        .header h1 { font-size: 2.5rem; color: #fff; margin-bottom: 0.5rem; }
        .header p { color: var(--text-muted); }

        .app-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
        @media (max-width: 900px) { .app-grid { grid-template-columns: 1fr; } }

        .card { background-color: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; display: flex; flex-direction: column; }

        .controls { display: flex; gap: 1rem; margin-bottom: 1rem; }
        select { flex: 1; background-color: var(--bg-color); color: var(--text-main); border: 1px solid var(--border); padding: 0.5rem; border-radius: 6px; font-size: 0.9rem; outline: none; }
        select:focus { border-color: var(--accent); }

        textarea { width: 100%; height: 400px; background-color: var(--bg-color); color: var(--text-main); border: 1px solid var(--border); border-radius: 6px; padding: 1rem; font-family: 'Courier New', Courier, monospace; font-size: 0.9rem; resize: none; margin-bottom: 1rem; outline: none; }
        textarea:focus { border-color: var(--accent); }

        button { width: 100%; padding: 0.75rem; border: none; border-radius: 6px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: 0.2s; }
        .btn-primary { background-color: var(--accent); color: #fff; }
        .btn-primary:hover { background-color: var(--accent-hover); }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

        .btn-success { background-color: var(--success); color: #fff; width: auto; padding: 0.5rem 1rem; font-size: 0.85rem; }
        .btn-success:hover { background-color: var(--success-hover); }

        .result-header { display: flex; justify-content: space-between; items-center: center; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); }
        .result-header h3 { color: #fff; }

        .markdown-body { overflow-y: auto; max-height: 400px; padding-right: 0.5rem; }
        .markdown-body h2, .markdown-body h3 { color: #fff; margin-top: 1rem; margin-bottom: 0.5rem; }
        .markdown-body p, .markdown-body ul { margin-bottom: 1rem; color: var(--text-main); }
        .markdown-body ul { padding-left: 2rem; }
        .markdown-body pre { background-color: var(--bg-color); padding: 1rem; border-radius: 6px; overflow-x: auto; margin-bottom: 1rem; border: 1px solid var(--border); }

        /* Custom scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--card-bg); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
    </style>
</head>
<body>
    <div id="root"></div>

    <script type="text/babel">
        function App() {
            const [code, setCode] = React.useState('');
            const [language, setLanguage] = React.useState('C++');
            const [persona, setPersona] = React.useState('senior');
            const [loading, setLoading] = React.useState(false);
            const [result, setResult] = React.useState('');
            const [rawMarkdown, setRawMarkdown] = React.useState('');

            const analyzeCode = async () => {
                if (!code.trim()) return alert("Please enter some code.");
                setLoading(true);
                setResult('');

                try {
                    const res = await fetch('/analyze', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ code, language, persona })
                    });

                    if (!res.ok) throw new Error("Server connection failed.");

                    const data = await res.json();
                    setRawMarkdown(data.analysis);
                    setResult(marked.parse(data.analysis));

                    // Apply syntax highlighting after render
                    setTimeout(() => Prism.highlightAll(), 0);
                } catch (error) {
                    alert(error.message);
                } finally {
                    setLoading(false);
                }
            };

            const downloadPDF = async () => {
                try {
                    const res = await fetch('/api/download', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ feedback: rawMarkdown, language })
                    });

                    if (res.ok) {
                        const blob = await res.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `Code_Review_${language}.pdf`;
                        a.click();
                    } else {
                        alert("PDF generation failed.");
                    }
                } catch (e) {
                    alert("Network error.");
                }
            };

            return (
                <div className="container">
                    <div className="header">
                        <h1>AI Code Lab Pro</h1>
                        <p>Intelligent Logic & Complexity Reviewer</p>
                    </div>

                    <div className="app-grid">
                        <div className="card">
                            <div className="controls">
                                <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                                    <option value="C++">C++</option>
                                    <option value="Python">Python</option>
                                    <option value="Java">Java</option>
                                </select>
                                <select value={persona} onChange={(e) => setPersona(e.target.value)}>
                                    <option value="senior">Senior Engineer</option>
                                    <option value="tutor">Coding Tutor</option>
                                </select>
                            </div>

                            <textarea 
                                placeholder="// Paste your code here..."
                                value={code}
                                onChange={(e) => setCode(e.target.value)}
                                spellCheck="false"
                            />

                            <button 
                                className="btn-primary" 
                                onClick={analyzeCode} 
                                disabled={loading}
                            >
                                {loading ? 'Analyzing...' : 'Analyze Code'}
                            </button>
                        </div>

                        <div className="card">
                            <div className="result-header">
                                <h3>Analysis Report</h3>
                                {result && (
                                    <button className="btn-success" onClick={downloadPDF}>
                                        📥 Download PDF
                                    </button>
                                )}
                            </div>

                            <div className="markdown-body">
                                {!result && !loading && <p style={{color: '#8b949e', textAlign: 'center', marginTop: '4rem'}}>Awaiting code submission...</p>}
                                {loading && <p style={{color: '#58a6ff', textAlign: 'center', marginTop: '4rem'}}>Gemini is reviewing...</p>}
                                {result && <div dangerouslySetInnerHTML={{ __html: result }} />}
                            </div>
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

@app.get("/")
async def get_index():
    return HTMLResponse(content=html_content)

@app.post("/analyze")
async def analyze_code(req: CodeRequest):
    role = "Senior Software Engineer" if req.persona == "senior" else "Patient Coding Tutor"
    prompt = f"Act as a {role}. Analyze this {req.language} code for logic, efficiency, and time complexity. Use markdown for formatting:\n\n{req.code}"

    response = model.generate_content(prompt)
    return {"analysis": response.text}

@app.post("/api/download")
async def download_pdf(req: PDFRequest):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Title
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, f"Code Review Report - {req.language}", ln=True, align='C')
        pdf.ln(5)

        # Body
        pdf.set_font("Helvetica", size=11)

        # 1. Clean up markdown formatting
        clean_text = req.feedback.replace('**', '').replace('```', '')

        # 2. THE FIX: Force the text into safe characters so FPDF doesn't crash
        safe_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')

        pdf.multi_cell(0, 7, safe_text)

        pdf_bytes = bytes(pdf.output())
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Code_Review_{req.language}.pdf"}
        )
    except Exception as e:
        print(f"PDF Generation Error: {str(e)}")
        return Response(status_code=500, content="Failed to generate PDF")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
