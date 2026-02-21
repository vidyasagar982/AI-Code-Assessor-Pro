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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Fira+Code:wght@400;500&display=swap');

        :root {
            --bg: #0b0f19;
            --surface: #111827;
            --border: #1f2937;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --text: #f3f4f6;
            --text-muted: #9ca3af;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body { 
            font-family: 'Inter', sans-serif; 
            background-color: var(--bg); 
            color: var(--text); 
            height: 100vh; 
            display: flex; 
            flex-direction: column; 
            overflow: hidden; 
        }

        /* Navbar */
        .navbar {
            padding: 1rem 1.5rem;
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            z-index: 10;
        }

        .navbar h1 {
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(to right, #60a5fa, #a855f7);
            -webkit-background-clip: text;
            color: transparent;
            letter-spacing: -0.5px;
        }

        .navbar p { font-size: 0.875rem; color: var(--text-muted); font-weight: 600; }

        /* Main Workspace Grid */
        .workspace {
            flex: 1;
            display: flex;
            gap: 1rem;
            padding: 1rem;
            overflow: hidden;
        }

        @media (max-width: 768px) {
            .workspace { flex-direction: column; overflow-y: auto; }
            body { height: auto; min-height: 100vh; }
        }

        /* Panels */
        .panel {
            flex: 1;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }

        .panel-header {
            padding: 0.75rem 1rem;
            background: rgba(17, 24, 39, 0.8);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .controls { display: flex; gap: 0.5rem; width: 100%; }

        select {
            background: #1f2937;
            color: white;
            border: 1px solid #374151;
            padding: 0.5rem 0.75rem;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            outline: none;
            cursor: pointer;
            transition: all 0.2s;
        }

        select:hover, select:focus { border-color: var(--primary); }

        /* Editor Area */
        textarea {
            flex: 1;
            width: 100%;
            background: transparent;
            border: none;
            color: #a5b4fc;
            padding: 1rem;
            font-family: 'Fira Code', monospace;
            font-size: 0.9rem;
            line-height: 1.5;
            resize: none;
            outline: none;
        }

        /* Buttons */
        .btn {
            padding: 0.85rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background: var(--primary);
            color: white;
            margin: 1rem;
            box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
        }

        .btn-primary:hover:not(:disabled) {
            background: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 6px 12px -2px rgba(59, 130, 246, 0.4);
        }

        .btn-primary:disabled { opacity: 0.7; cursor: not-allowed; }

        .btn-success {
            background: rgba(16, 185, 129, 0.1);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.2);
            padding: 0.4rem 0.8rem;
            font-size: 0.75rem;
            border-radius: 6px;
        }

        .btn-success:hover { background: rgba(16, 185, 129, 0.2); transform: translateY(-1px); }

        /* Output Area */
        .output-area {
            flex: 1;
            overflow-y: auto;
            padding: 1.5rem;
        }

        /* Animations */
        .spinner {
            border: 3px solid rgba(255,255,255,0.1);
            border-top: 3px solid #fff;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
        }

        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: var(--text-muted);
            text-align: center;
            opacity: 0.6;
        }

        .empty-state svg { width: 48px; height: 48px; margin-bottom: 1rem; }

        /* Beautiful Markdown Formatting */
        .markdown-body h2 { color: #fff; font-size: 1.5rem; margin-top: 1rem; margin-bottom: 0.75rem; border-bottom: 1px solid var(--border); padding-bottom: 0.25rem; }
        .markdown-body h3 { color: #e2e8f0; font-size: 1.25rem; margin-top: 1rem; margin-bottom: 0.5rem; }
        .markdown-body p, .markdown-body li { color: #cbd5e1; line-height: 1.7; margin-bottom: 1rem; }
        .markdown-body ul { padding-left: 1.5rem; margin-bottom: 1rem; }
        .markdown-body pre { background: #0b0f19 !important; padding: 1rem; border-radius: 8px; border: 1px solid var(--border); overflow-x: auto; margin: 1rem 0; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); }
        .markdown-body code { font-family: 'Fira Code', monospace; font-size: 0.85rem; }
        .markdown-body p > code, .markdown-body li > code { background: rgba(59, 130, 246, 0.1); color: #93c5fd; padding: 0.2rem 0.4rem; border-radius: 4px; }

        /* Custom Scrollbars */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #4b5563; }
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
                <React.Fragment>
                    <div className="navbar">
                        <h1>AI Code Lab Pro</h1>
                        <p>v2.0 Beta</p>
                    </div>

                    <div className="workspace">
                        {/* Editor Panel */}
                        <div className="panel">
                            <div className="panel-header">
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
                            </div>

                            <textarea 
                                placeholder="// Write or paste your code here...&#10;// The AI will analyze logic, efficiency, and time complexity."
                                value={code}
                                onChange={(e) => setCode(e.target.value)}
                                spellCheck="false"
                            />

                            <button 
                                className="btn btn-primary" 
                                onClick={analyzeCode} 
                                disabled={loading}
                            >
                                {loading ? (
                                    <React.Fragment>
                                        <div className="spinner"></div>
                                        Analyzing Logic...
                                    </React.Fragment>
                                ) : (
                                    <React.Fragment>
                                        🚀 Run AI Analysis
                                    </React.Fragment>
                                )}
                            </button>
                        </div>

                        {/* Results Panel */}
                        <div className="panel">
                            <div className="panel-header" style={{ justifyContent: 'space-between' }}>
                                <h3 style={{ fontSize: '0.9rem', color: '#cbd5e1', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    ✨ Analysis Report
                                </h3>
                                {result && (
                                    <button className="btn btn-success" onClick={downloadPDF}>
                                        📥 Export PDF
                                    </button>
                                )}
                            </div>

                            <div className="output-area markdown-body">
                                {!result && !loading && (
                                    <div className="empty-state">
                                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
                                        <p>Awaiting code submission...</p>
                                    </div>
                                )}
                                {result && <div dangerouslySetInnerHTML={{ __html: result }} />}
                            </div>
                        </div>
                    </div>
                </React.Fragment>
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
