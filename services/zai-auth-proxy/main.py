"""
Z.ai Authentication Proxy

This service captures Z.ai session tokens after OAuth login
and provides a proxy endpoint that uses those tokens for API calls.
"""

import json
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx

logger = logging.getLogger(__name__)

# Storage for session tokens
TOKEN_STORE = Path(__file__).parent / "tokens"
TOKEN_STORE.mkdir(exist_ok=True)

app = FastAPI(title="Z.ai Auth Proxy", version="1.0.0")

# Token cache
_active_tokens = {}


class TokenInfo(BaseModel):
    token: str
    expires_at: Optional[str] = None
    user_info: Optional[dict] = None


class ChatRequest(BaseModel):
    model: str
    messages: list
    max_tokens: int = 512
    temperature: float = 0.7
    stream: bool = False


def get_token_path() -> Path:
    return TOKEN_STORE / "session_token.json"


def load_token() -> Optional[TokenInfo]:
    token_path = get_token_path()
    if token_path.exists():
        try:
            data = json.loads(token_path.read_text())
            return TokenInfo(**data)
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
    return None


def save_token_file(token_info: TokenInfo):
    token_path = get_token_path()
    token_path.write_text(json.dumps({
        "token": token_info.token,
        "expires_at": token_info.expires_at,
        "user_info": token_info.user_info
    }, indent=2))
    logger.info(f"Token saved to {token_path}")


def get_active_token() -> Optional[str]:
    if _active_tokens.get("current"):
        return _active_tokens["current"]["token"]
    token_info = load_token()
    if token_info:
        _active_tokens["current"] = {
            "token": token_info.token,
            "expires_at": token_info.expires_at,
            "user_info": token_info.user_info
        }
        return token_info.token
    return None


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Z.ai Authentication Proxy</title>
    <style>
        body { font-family: system-ui; max-width: 600px; margin: 100px auto; padding: 20px; text-align: center; }
        .card { border: 1px solid #e0e0e0; border-radius: 12px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .status { padding: 10px; border-radius: 8px; margin: 20px 0; }
        .status.authenticated { background: #d4edda; color: #155724; }
        .status.not-authenticated { background: #f8d7da; color: #721c24; }
        .btn { display: inline-block; padding: 12px 24px; background: #4285f4; color: white; text-decoration: none; border-radius: 6px; margin: 10px; cursor: pointer; border: none; }
        .btn:hover { background: #3367d6; }
        .btn.secondary { background: #6c757d; }
        .info { margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 8px; font-size: 14px; text-align: left; }
        code { background: #e9ecef; padding: 2px 6px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🔐 Z.ai Authentication Proxy</h1>
        <div id="status" class="status not-authenticated">Not authenticated</div>
        <div id="auth-section">
            <p>Click the button below to authenticate with your Z.ai account:</p>
            <a href="https://chat.z.ai" target="_blank" class="btn">Open Z.ai to Login</a>
            <p style="font-size: 14px; color: #666; margin-top: 15px;">After logging in, come back and click "Capture Token" below.</p>
            <button onclick="captureToken()" class="btn">Capture Token from Browser</button>
        </div>
        <div class="info">
            <strong>Instructions:</strong>
            <ol style="text-align: left;">
                <li>Click "Open Z.ai to Login" above</li>
                <li>Sign in with your Google OAuth account</li>
                <li>Come back to this page</li>
                <li>Click "Capture Token from Browser"</li>
                <li>Paste your session token when prompted</li>
            </ol>
            <p style="margin-top: 15px;">
                <strong>To find your token:</strong><br>
                1. After logging in to Z.ai, open browser DevTools (F12)<br>
                2. Go to Console tab<br>
                3. Type: <code>localStorage.getItem('token')</code><br>
                4. Copy the output and paste it here
            </p>
        </div>
    </div>
    <script>
        async function checkStatus() {
            try {
                const response = await fetch('/auth/status');
                const data = await response.json();
                const statusEl = document.getElementById('status');
                const authSection = document.getElementById('auth-section');
                if (data.authenticated) {
                    statusEl.className = 'status authenticated';
                    statusEl.textContent = '✅ Authenticated as: ' + (data.email || 'User');
                    authSection.innerHTML = '<p>Session token is active and ready to use!</p><button onclick="testAPI()" class="btn">Test API Call</button><button onclick="invalidateToken()" class="btn secondary">Clear Token</button>';
                } else {
                    statusEl.className = 'status not-authenticated';
                    statusEl.textContent = 'Not authenticated';
                }
            } catch (e) { console.error(e); }
        }
        async function captureToken() {
            const token = prompt('Enter your Z.ai session token:\\n\\n(From browser console: localStorage.getItem("token"))');
            if (token) {
                try {
                    const response = await fetch('/auth/token', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ token: token })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        alert('✅ Token captured successfully!');
                        checkStatus();
                    } else {
                        alert('❌ Failed: ' + (data.detail || 'Unknown error'));
                    }
                } catch (e) { alert('❌ Error: ' + e.message); }
            }
        }
        async function testAPI() {
            try {
                const response = await fetch('/api/v1/chat/completions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: 'glm-4.7',
                        messages: [{ role: 'user', content: 'Say hello! This is a test.' }],
                        max_tokens: 50
                    })
                });
                const data = await response.json();
                if (response.ok) {
                    alert('✅ API Test Successful!\\n\\nResponse: ' + JSON.stringify(data, null, 2));
                } else {
                    alert('❌ API Test Failed:\\n\\n' + JSON.stringify(data, null, 2));
                }
            } catch (e) { alert('❌ Error: ' + e.message); }
        }
        async function invalidateToken() {
            if (confirm('Clear the stored token?')) {
                await fetch('/auth/token', { method: 'DELETE' });
                alert('Token cleared!');
                checkStatus();
            }
        }
        checkStatus();
        setInterval(checkStatus, 30000);
    </script>
</body>
</html>
    """


@app.get("/auth/status")
async def auth_status():
    token = get_active_token()
    if token:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://chat.z.ai/api/v1/users/user/settings",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    user_info = response.json()
                    return {"authenticated": True, "email": user_info.get("email"), "name": user_info.get("name")}
        except Exception as e:
            logger.warning(f"Failed to get user info: {e}")
        return {"authenticated": True}
    return {"authenticated": False}


@app.post("/auth/token")
async def save_token_endpoint(request: Request):
    data = await request.json()
    token = data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://chat.z.ai/api/models",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                token_info = TokenInfo(token=token)
                save_token_file(token_info)
                _active_tokens["current"] = {"token": token}
                logger.info("Session token saved successfully")
                return {"status": "success", "message": "Token saved"}
            raise HTTPException(status_code=401, detail=f"Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/auth/token")
async def invalidate_token():
    token_path = get_token_path()
    if token_path.exists():
        token_path.unlink()
    _active_tokens.pop("current", None)
    return {"status": "success", "message": "Token cleared"}


@app.post("/api/v1/chat/completions")
async def proxy_chat_completions(request: ChatRequest):
    token = get_active_token()
    if not token:
        raise HTTPException(status_code=401, detail="No active session token. Please authenticate first.")
    
    payload = {
        "model": request.model,
        "messages": request.messages,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "stream": request.stream
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://chat.z.ai/api/v2/chat/completions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (compatible; ZAI-Proxy/1.0)"
                },
                json=payload
            )
            if response.status_code == 200:
                return Response(content=response.content, status_code=200, media_type="text/event-stream")
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    token = get_active_token()
    return {"status": "healthy", "service": "zai-auth-proxy", "authenticated": token is not None}


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    uvicorn.run("main:app", host="127.0.0.1", port=8899, log_level="info")
