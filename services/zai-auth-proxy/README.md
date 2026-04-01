# Z.ai Authentication Proxy

This service captures Z.ai web chat session tokens and provides a proxy that uses those tokens for API calls, allowing you to use your "5 Hours Quota" from the web interface for application requests.

## How It Works

```
Your App → ZAI Auth Proxy → chat.z.ai API (with session token)
                ↓
         Uses Web Chat Quota ✅
```

## Quick Start

### 1. Start the Authentication Proxy

```bash
cd /home/ranj/Project_Chimera/services/zai-auth-proxy
./start.sh
```

The proxy will start on `http://127.0.0.1:8899`

### 2. Authenticate with Z.ai

1. Open your browser: `http://127.0.0.1:8899`
2. Click "Open Z.ai to Login"
3. Sign in with your Google OAuth account
4. After logging in, get your session token:
   - Press F12 (DevTools)
   - Go to Console tab
   - Type: `localStorage.getItem('token')`
   - Copy the output
5. Click "Capture Token" and paste the token
6. Verify authentication works with "Test API Call"

### 3. Configure Your Applications

Use the proxy endpoint instead of the direct Z.ai API:

```python
# Old: Direct API (requires resource package)
client = OpenAI(
    api_key="your-api-key",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

# New: Via proxy (uses web chat quota)
client = OpenAI(
    api_key="proxy",  # Not used, but required by OpenAI client
    base_url="http://127.0.0.1:8899/api/v1"
)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface for authentication |
| `/auth/status` | GET | Check authentication status |
| `/auth/token` | POST | Save session token |
| `/auth/token` | DELETE | Clear stored token |
| `/api/v1/chat/completions` | POST | Proxy for chat completions |
| `/health` | GET | Health check |

## Integration with NemoClaw

The proxy integrates with the existing privacy router:

```python
# In services/nemoclaw-orchestrator/llm/zai_client.py
# Add proxy support:

ZAI_PROXY_URL = "http://127.0.0.1:8899"

# When making requests:
if os.getenv("USE_ZAI_PROXY", "false").lower() == "true":
    base_url = f"{ZAI_PROXY_URL}/api/v1"
else:
    base_url = "https://open.bigmodel.cn/api/paas/v4/"
```

## Security Notes

- The proxy runs on localhost only (127.0.0.1)
- Session tokens are stored locally in `tokens/session_token.json`
- Tokens are not logged or transmitted anywhere else

## Troubleshooting

### "Invalid token" error
- Make sure you copied the entire token from localStorage
- Tokens can expire - you may need to re-authenticate

### "Client version outdated" error
- The proxy automatically handles this with fallback logic
- If persistent, try capturing a fresh token

### Proxy not working
- Check that the proxy service is running: `curl http://127.0.0.1:8899/health`
- Verify token is captured: Check `/auth/status`
- Check logs in the terminal where the proxy is running

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ZAI_PROXY_PORT` | 8899 | Port for the proxy service |
| `ZAI_PROXY_HOST` | 127.0.0.1 | Host to bind to |

## Files

```
zai-auth-proxy/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── start.sh            # Startup script
├── tokens/             # Stored session tokens (created at runtime)
└── README.md           # This file
```
