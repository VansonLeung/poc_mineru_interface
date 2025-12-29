# CORS Fix: Duplicate Access-Control-Allow-Origin Headers

## Problem

Browser error when accessing `https://oct-ext81-9.octopus-tech.com/api/v1/parse`:
```
[Error] Access-Control-Allow-Origin cannot contain more than one origin.
[Error] Fetch API cannot load https://oct-ext81-9.octopus-tech.com/api/v1/parse due to access control checks.
```

## Root Cause

**Duplicate CORS headers** were being added:
1. ✅ **Nginx** was adding CORS headers via `add_header` directives
2. ✅ **FastAPI backend** was adding CORS headers via `CORSMiddleware`

This resulted in multiple `Access-Control-Allow-Origin` headers in the response, which browsers reject (only one header is allowed).

## Solution

**Removed CORS headers from Nginx configuration**, letting FastAPI backend handle CORS exclusively through its `CORSMiddleware`.

### Changes Made

**File**: `/opt/homebrew/etc/nginx/servers/t1.conf`

**oct-ext81-8 server block (line ~354-380)**:
- ❌ **Removed**: CORS `add_header` directives
- ❌ **Removed**: `if ($request_method = OPTIONS)` block
- ✅ **Added comment**: "CORS handled by FastAPI backend - do not add headers here to avoid duplicates"

**oct-ext81-9 server block (line ~390-419)**:
- ❌ **Removed**: CORS `add_header` directives  
- ❌ **Removed**: `if ($request_method = OPTIONS)` block
- ✅ **Added comment**: "CORS handled by FastAPI backend - do not add headers here to avoid duplicates"

**Kept**:
- Large file upload settings (`client_max_body_size 500M`)
- Long timeout settings (`proxy_*_timeout 2400s`)
- WebSocket proxy settings
- Standard proxy headers

## FastAPI CORS Configuration

The backend already has proper CORS handling in `backend/src/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_normalized,  # Default: ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=settings.cors_allow_credentials,  # Default: False
)
```

**Settings** (`backend/src/config/settings.py`):
- `cors_allow_origins`: Default `["*"]` (allows all origins)
- `cors_allow_credentials`: Default `False`
- Can be configured via `.env` file

## Next Steps

**To apply the fix**, reload Nginx:

```bash
# Test configuration (requires password)
sudo nginx -t

# If test passes, reload Nginx
sudo nginx -s reload
```

**Or restart Nginx**:
```bash
# Stop Nginx
sudo nginx -s stop

# Start Nginx
sudo nginx
```

## Verification

After reloading Nginx, test the frontend:

1. Open http://localhost:28110/ (frontend dev server)
2. Check "Async Mode" checkbox
3. Upload a file (e.g., IMG_3103.jpg)
4. Verify no CORS errors in browser console
5. Job should submit successfully

**Expected browser network response headers**:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: *
Access-Control-Allow-Credentials: false
```

**Should see ONLY ONE `Access-Control-Allow-Origin` header** (from FastAPI, not Nginx).

## Why This Works

**Best Practice**: Handle CORS at the application layer (FastAPI), not at the proxy layer (Nginx).

**Benefits**:
- ✅ Single source of truth for CORS configuration
- ✅ No duplicate headers
- ✅ FastAPI middleware properly handles preflight OPTIONS requests
- ✅ Easier to configure via environment variables
- ✅ Consistent CORS behavior across all routes

**When to use Nginx CORS**:
- Only if the backend does NOT handle CORS
- For static file servers without application logic
- For multiple backends with different CORS needs

**Current setup**: Backend handles CORS → Nginx just proxies requests → No CORS headers in Nginx

## Configuration Reference

### Backend CORS (.env file)

```bash
# Allow all origins (default)
CORS_ALLOW_ORIGINS=*

# Allow specific origin
CORS_ALLOW_ORIGINS=https://oct-ext81-8.octopus-tech.com

# Allow multiple origins (comma-separated)
CORS_ALLOW_ORIGINS=https://oct-ext81-8.octopus-tech.com,https://oct-ext81-9.octopus-tech.com

# Allow credentials (cookies)
CORS_ALLOW_CREDENTIALS=true
```

### Updated Nginx Configuration

```nginx
server {
    listen 80;
    server_name oct-ext81-9.octopus-tech.com;

    location / {
        proxy_pass http://localhost:28109;

        # Allow large file uploads and long-running parse responses
        client_max_body_size 500M;
        proxy_connect_timeout 30s;
        proxy_send_timeout 2400s;
        proxy_read_timeout 2400s;
        send_timeout 2400s;

        # CORS handled by FastAPI backend - do not add headers here to avoid duplicates

        # Proxy settings for WebSocket
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Set headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Additional WebSocket support
        proxy_buffering off;
    }
}
```

## Troubleshooting

### If CORS errors persist:

1. **Clear browser cache**: Hard refresh (Cmd+Shift+R / Ctrl+Shift+F5)
2. **Check backend is running**: `curl http://localhost:28109/health`
3. **Verify Nginx reloaded**: `ps aux | grep nginx`
4. **Check response headers**:
   ```bash
   curl -I https://oct-ext81-9.octopus-tech.com/health
   ```
5. **Check for multiple headers**:
   ```bash
   curl -v https://oct-ext81-9.octopus-tech.com/health 2>&1 | grep -i access-control
   ```

### If still seeing duplicate headers:

- Check if there are other Nginx config files adding CORS headers
- Verify backend `.env` file CORS settings
- Check if there's caching proxy between client and server

## Status

✅ **Configuration Updated**  
⏳ **Nginx Reload Required** (needs sudo password)  
⏳ **Testing Required**

Once Nginx is reloaded, the CORS error should be resolved!
