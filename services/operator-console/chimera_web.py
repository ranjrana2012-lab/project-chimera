from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
import uvicorn
import sys
import os
from dataclasses import dataclass

from chimera_core import ChimeraCore, spawn_voice

MAX_INPUT_CHARS = int(os.getenv("CHIMERA_WEB_MAX_INPUT_CHARS", "2000"))


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int


def get_server_config() -> ServerConfig:
    return ServerConfig(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8080")),
    )


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

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/api/process")
async def process(req: Request):
    data = await req.json()
    raw_text = data.get("text")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    text = raw_text.strip()
    if len(text) > MAX_INPUT_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"text must be {MAX_INPUT_CHARS} characters or fewer",
        )
    
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
    return FileResponse("static/projection.html")

if __name__ == "__main__":
    config = get_server_config()
    uvicorn.run(app, host=config.host, port=config.port)
