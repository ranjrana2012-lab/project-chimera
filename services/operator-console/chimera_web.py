from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
import sys
import os

from chimera_core import ChimeraCore, spawn_voice

app = FastAPI()
chimera = ChimeraCore()
chimera.load_models()

# Global state tracker for projection sync & session history
app.state.history = []
app.state.latest_response = {
    "text": "",
    "sentiment": "NEUTRAL",
    "strategy": "standard_response",
    "response": "Awaiting initial dialogue..."
}

@app.get("/")
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chimera Operator Console</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #38bdf8;
                --secondary: #818cf8;
                --bg: #0f172a;
                --panel: rgba(30, 41, 59, 0.75);
                --text: #f8fafc;
            }
            body { 
                background: linear-gradient(135deg, #020617 0%, var(--bg) 100%); 
                color: var(--text); 
                font-family: 'Inter', sans-serif; 
                display: flex; 
                flex-direction: column; 
                align-items: center; 
                justify-content: center; 
                height: 100vh; 
                margin: 0; 
                overflow: hidden;
                transition: background 1.5s ease-in-out;
            }
            .glow {
                position: absolute;
                width: 400px;
                height: 400px;
                background: radial-gradient(circle, var(--secondary) 0%, transparent 70%);
                filter: blur(100px);
                opacity: 0.15;
                z-index: 0;
                transition: background 1.5s ease-in-out, opacity 1s;
            }
            .container { 
                position: relative;
                z-index: 1;
                background: var(--panel); 
                backdrop-filter: blur(16px); 
                -webkit-backdrop-filter: blur(16px);
                padding: 2.5rem; 
                border-radius: 1.5rem; 
                border: 1px solid rgba(255,255,255,0.1); 
                width: 600px; 
                max-width: 90%; 
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); 
            }
            h1 { 
                font-size: 2.5rem; 
                font-weight: 800;
                margin-top: 0;
                background: -webkit-linear-gradient(0deg, var(--primary), var(--secondary)); 
                -webkit-background-clip: text; 
                -webkit-text-fill-color: transparent; 
                text-align: center;
            }
            .subtitle {
                text-align: center;
                color: #94a3b8;
                margin-top: -1rem;
                margin-bottom: 2rem;
            }
            input { 
                width: 100%; 
                padding: 1.2rem; 
                margin-bottom: 1rem; 
                border-radius: 0.75rem; 
                border: 1px solid #475569; 
                background: #1e293b; 
                color: white; 
                font-size: 1rem; 
                box-sizing: border-box;
                transition: border-color 0.3s, box-shadow 0.3s;
                font-family: 'Inter', sans-serif;
            }
            input:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
            }
            button { 
                width: 100%; 
                padding: 1.2rem; 
                background: linear-gradient(135deg, #3b82f6, #8b5cf6); 
                color: white; 
                border: none; 
                border-radius: 0.75rem; 
                font-size: 1.1rem; 
                font-weight: 600; 
                cursor: pointer; 
                transition: transform 0.2s, box-shadow 0.2s; 
                font-family: 'Inter', sans-serif;
            }
            button:hover { 
                transform: translateY(-2px); 
                box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4);
            }
            button:active {
                transform: translateY(0);
            }
            #output { 
                margin-top: 2rem; 
                padding: 1.5rem; 
                border-radius: 0.75rem; 
                background: rgba(15, 23, 42, 0.8); 
                min-height: 100px; 
                font-size: 1.05rem; 
                border-left: 4px solid var(--primary); 
                line-height: 1.6;
                transition: opacity 0.3s ease;
            }
            .meta { 
                font-size: 0.85rem; 
                color: #64748b; 
                margin-top: 1rem; 
                display: flex;
                justify-content: space-between;
                border-top: 1px solid #334155;
                padding-top: 0.5rem;
            }
            .spinner { 
                display: none; 
                margin: 2rem auto; 
                width: 40px; 
                height: 40px; 
                border: 4px solid rgba(255,255,255,0.1); 
                border-radius: 50%; 
                border-top-color: var(--primary); 
                animation: spin 1s ease-in-out infinite; 
            }
            @keyframes spin { to { transform: rotate(360deg); } }
            
            .badge {
                display: inline-block;
                padding: 0.2rem 0.6rem;
                border-radius: 9999px;
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .badge-primary { background: rgba(56, 189, 248, 0.2); color: #7dd3fc; }
            .badge-strategy { background: rgba(139, 92, 246, 0.2); color: #c4b5fd; }
        </style>
    </head>
    <body>
        <div class="glow"></div>
        <div class="container">
            <h1>Chimera Live</h1>
            <div class="subtitle">AI Operator Dashboard • <a href="/projection" target="_blank" style="color:var(--primary);text-decoration:none;">Open Projection</a> • <a href="/api/export" target="_blank" style="color:#10b981;text-decoration:none;">Download Analytics CSV</a></div>
            
            <input type="text" id="userInput" placeholder="Type simulated audience feedback..." autocomplete="off"/>
            <button onclick="send()" id="submitBtn">Compute Generative Response</button>
            <div class="spinner" id="spinner"></div>
            
            <div id="output">
                <span style="color: #94a3b8;">System initialized and listening... Type above to begin.</span>
            </div>
        </div>
        
        <script>
            async function send() {
                const text = document.getElementById('userInput').value;
                if (!text) return;
                
                const btn = document.getElementById('submitBtn');
                btn.disabled = true;
                btn.style.opacity = '0.7';
                
                document.getElementById('spinner').style.display = 'block';
                document.getElementById('output').style.opacity = '0.5';
                
                try {
                    const res = await fetch('/api/process', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({text: text})
                    });
                    const data = await res.json();
                    
                    document.getElementById('spinner').style.display = 'none';
                    document.getElementById('output').style.opacity = '1';
                    
                    document.getElementById('output').innerHTML = `
                        <div style="margin-bottom: 1rem;">
                            <span class="badge badge-strategy">${data.strategy}</span>
                            <span class="badge badge-primary" style="margin-left: 0.5rem;">${data.sentiment} (${(data.score*100).toFixed(1)}%)</span>
                        </div>
                        <div style="color: var(--text); font-size: 1.15rem; font-style: italic;">
                            "${data.response}"
                        </div>
                        <div class="meta">
                            <span>Latency: ${(data.latency_ms).toFixed(0)} ms</span>
                            <span>🔉 Audio Broadcasted</span>
                        </div>
                    `;
                    
                    // Virtual DMX Lighting Simulation Transitions
                    if (data.strategy === 'momentum_build') {
                        document.body.style.background = 'linear-gradient(135deg, #450a0a 0%, #0f172a 100%)';
                        document.querySelector('.glow').style.background = 'radial-gradient(circle, #f43f5e 0%, transparent 70%)';
                        document.querySelector('.glow').style.opacity = '0.35';
                    } else if (data.strategy === 'supportive_care') {
                        document.body.style.background = 'linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%)';
                        document.querySelector('.glow').style.background = 'radial-gradient(circle, #38bdf8 0%, transparent 70%)';
                        document.querySelector('.glow').style.opacity = '0.25';
                    } else {
                        document.body.style.background = 'linear-gradient(135deg, #020617 0%, var(--bg) 100%)';
                        document.querySelector('.glow').style.background = 'radial-gradient(circle, var(--secondary) 0%, transparent 70%)';
                        document.querySelector('.glow').style.opacity = '0.15';
                    }
                } catch (e) {
                    document.getElementById('spinner').style.display = 'none';
                    document.getElementById('output').style.opacity = '1';
                    document.getElementById('output').innerHTML = `<span style="color: #f87171;">Error processing request. Ensure Chimera backend is healthy.</span>`;
                } finally {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                }
            }
            
            document.getElementById('userInput').addEventListener('keypress', function (e) {
                if (e.key === 'Enter') send();
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/process")
async def process(req: Request):
    data = await req.json()
    text = data.get("text", "")
    
    import time
    start = time.time()
    
    # Process through core
    sentiment = chimera.analyze_sentiment(text)
    strategy = chimera.select_strategy(sentiment)
    response = chimera.generate_response(text, strategy)
    
    # Trigger broadcast voice
    spawn_voice(response)
    
    latency = (time.time() - start) * 1000
    
    app.state.latest_response = {
        "text": text,
        "sentiment": sentiment['label'],
        "score": sentiment['score'],
        "strategy": strategy,
        "response": response,
        "latency_ms": latency
    }
    
    app.state.history.append({
        "timestamp": time.time(),
        "input": text,
        "sentiment": sentiment['label'],
        "score": sentiment['score'],
        "strategy": strategy,
        "latency_ms": latency
    })
    
    return app.state.latest_response

@app.get("/api/state")
async def get_state():
    return app.state.latest_response

@app.get("/api/export")
def export_history():
    from fastapi.responses import PlainTextResponse
    import io, csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['timestamp', 'input', 'sentiment', 'confidence_score', 'strategy_routed', 'latency_ms'])
    
    for row in app.state.history:
        writer.writerow([row['timestamp'], row['input'], row['sentiment'], row['score'], row['strategy'], row['latency_ms']])
        
    return PlainTextResponse(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=chimera_analytics.csv"})

@app.get("/projection")
def projection_overlay():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chimera Live Caption Projection</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@700;900&display=swap" rel="stylesheet">
        <style>
            body { 
                background: #000000; 
                margin: 0; 
                overflow: hidden; 
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Inter', sans-serif;
            }
            .caption-box {
                width: 90%;
                text-align: center;
                color: #ffffff;
                font-size: 4rem;
                font-weight: 700;
                text-shadow: 0 4px 20px rgba(255,255,255,0.2);
                transition: opacity 0.5s;
            }
            .strategy-indicator {
                position: absolute;
                bottom: 2rem;
                right: 2rem;
                font-size: 1.5rem;
                color: #555;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 0.2rem;
            }
            .bsl-container {
                position: absolute;
                bottom: 2rem;
                left: 2rem;
                border: 2px dashed #475569;
                padding: 1.5rem;
                background: rgba(15, 23, 42, 0.8);
                color: #94a3b8;
                font-size: 0.9rem;
                text-align: center;
                border-radius: 0.5rem;
                letter-spacing: 0.1em;
            }
            .pulse { animation: fadePulse 2s infinite; }
            @keyframes fadePulse { 0% { opacity: 0.8; } 50% { opacity: 1; } 100% { opacity: 0.8; } }
        </style>
    </head>
    <body>
        <div class="caption-box" id="caption">SYSTEM INITIALIZING...</div>
        
        <div class="bsl-container">
            [ PHASE 2: BSL AVATAR RENDER TARGET ]<br>
            <span id="bsl-text" style="font-size: 0.85rem; color: #38bdf8; font-weight: bold; margin-top: 10px; display: block;">* STANDBY *</span>
        </div>
        
        <div class="strategy-indicator" id="strategy">STANDBY</div>
        <script>
            let lastResponse = "";
            const bslDictionary = {
                'momentum_build': '* EXCITED ANIMATION SEQUENCE *',
                'supportive_care': '* CALMING NURTURING GESTURES *',
                'standard_response': '* PROFESSIONAL NEUTRAL POSTURE *'
            };
            
            setInterval(async () => {
                try {
                    const res = await fetch('/api/state');
                    const data = await res.json();
                    if (data.response !== lastResponse) {
                        lastResponse = data.response;
                        const cap = document.getElementById('caption');
                        cap.style.opacity = '0';
                        setTimeout(() => {
                            cap.innerText = `"${data.response}"`;
                            cap.style.opacity = '1';
                        }, 500);
                        document.getElementById('strategy').innerText = data.strategy.replace('_', ' ');
                        document.getElementById('bsl-text').innerText = bslDictionary[data.strategy] || '* WAITING *';
                        
                        if (data.strategy === 'momentum_build') { document.getElementById('strategy').style.color = '#ef4444'; }
                        else if (data.strategy === 'supportive_care') { document.getElementById('strategy').style.color = '#3b82f6'; }
                        else { document.getElementById('strategy').style.color = '#555'; }
                    }
                } catch (e) {}
            }, 600);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host=host, port=port)
