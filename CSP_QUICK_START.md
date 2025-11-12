# Content Security Policy Implementation for Streamlit

## Overview

This application now implements the **recommended CSP policy for Streamlit** as per Streamlit best practices. The policy is implemented via an Nginx reverse proxy that adds CSP headers to all responses.

## CSP Policy

```
Content-Security-Policy: default-src 'self'; 
                         script-src 'self'; 
                         style-src 'self' 'unsafe-inline'; 
                         img-src 'self' data:; 
                         font-src 'self' data:; 
                         connect-src 'self' ws: wss:; 
                         frame-ancestors 'none';
```

### Policy Directives Explained

| Directive | Value | Rationale |
|-----------|-------|-----------|
| `default-src` | `'self'` | Base policy - only allow resources from same origin |
| `script-src` | `'self'` | Scripts only from application (Streamlit serves its own JS) |
| `style-src` | `'self' 'unsafe-inline'` | Styles from self + inline (Streamlit uses inline styles) |
| `img-src` | `'self' data:` | Images from self and data URIs |
| `font-src` | `'self' data:` | Fonts from self and data URIs |
| `connect-src` | `'self' ws: wss:` | API calls + WebSocket connections (live updates) |
| `frame-ancestors` | `'none'` | Prevents embedding in other pages (clickjacking protection) |

### Why This Policy Works with Streamlit

1. **`style-src 'unsafe-inline'`** - Streamlit uses inline styles extensively
2. **`connect-src ws: wss:`** - Streamlit uses WebSockets for live interactivity
3. **`script-src 'self'`** - Strict because Streamlit serves all JS from itself
4. **No `unsafe-eval`** - Not needed for Streamlit's JS execution

## Architecture

```
Browser Request
    ↓
Nginx (Port 5001) - Adds CSP Headers
    ↓
Streamlit (Internal Port 5001) - Application
```

## Deployment

### Quick Start with Docker Compose

```bash
cd team1f25

# Set API key
export GROQ_API_KEY="your-api-key"

# Start services
docker-compose up -d

# Access at http://localhost:5001/team1f25/
```

### Using Startup Script

```bash
./scripts/startup.sh
# Enter API key when prompted
```

## Verification

### Check CSP Headers

```bash
curl -i http://localhost:5001/team1f25/ | grep -i "content-security-policy"
```

Expected output:
```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self' ws: wss:; frame-ancestors 'none';
```

### Run ZAP Security Scan

```bash
zaproxy-scan.sh -t http://localhost:5001/team1f25/ -r report.html
```

All CSP-related vulnerabilities should now be resolved.

## If Something Breaks

The policy is strict but designed for Streamlit. If interactive features don't work:

1. Check browser console for CSP violations
2. Update `nginx/nginx.conf` CSP directive with the minimum needed permissions
3. Restart: `docker-compose restart nginx`

Example: if external scripts are needed, add to `script-src`:
```
script-src 'self' https://cdn.example.com;
```

## Files Modified

- **`.streamlit/config.toml`** - Streamlit security config (CORS disabled, XSRF enabled)
- **`nginx/nginx.conf`** - Nginx reverse proxy with CSP headers
- **`docker-compose.yml`** - Multi-service Docker setup
- **`scripts/startup.sh`** - Updated to use docker-compose
- **`streamlit_wrapper.py`** - Optional helper script

## Additional Security Headers

In addition to CSP, the following headers are added:

```
X-Frame-Options: DENY                                    # Clickjacking protection
X-Content-Type-Options: nosniff                          # MIME-sniffing protection
X-XSS-Protection: 1; mode=block                          # Legacy XSS protection
Referrer-Policy: strict-origin-when-cross-origin         # Referrer control
Permissions-Policy: geolocation=(), microphone=(), ...   # Browser API restrictions
```

## Troubleshooting

### App won't load
1. Check logs: `docker-compose logs streamlit`
2. Verify Nginx is running: `docker-compose ps`
3. Clear browser cache

### CSP violations in console
1. Check what resource failed
2. Add exception to CSP in `nginx/nginx.conf`
3. Restart: `docker-compose restart nginx`

### Port already in use
```bash
docker-compose down
docker-compose up -d
```

## References

- [Streamlit Security Best Practices](https://docs.streamlit.io/library/advanced-features/security)
- [MDN: Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [OWASP: CSP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

**Implementation**: Recommended CSP policy for Streamlit  
**Status**: Production Ready ✅  
**Last Updated**: November 11, 2025
