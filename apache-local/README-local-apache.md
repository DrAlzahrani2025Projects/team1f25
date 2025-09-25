# Local Apache reverse proxy (Windows/macOS)

This is a lightweight test harness to validate your path-based proxying to the Windows-hosted app without touching the production server.

It runs Apache httpd in a Docker container and proxies:
- `/team1f25/` → `http://host.docker.internal:5001/team1f25/` (Streamlit)
- `/team1f25-jupyter/` → `http://host.docker.internal:8888/team1f25-jupyter/` (Jupyter)

Prereqs:
- Docker Desktop running
- Your app container running locally and listening on ports 5001 and 8888

## PowerShell usage

```powershell
# from repo root
$img = "httpd:2.4"; docker pull $img

# or simply use the helper script (optional port):
./apache-local/start-proxy.ps1 -Port 8080

# check logs
docker logs --tail 80 $cid

# test
Invoke-WebRequest http://localhost:8080/team1f25/ -UseBasicParsing | Select-Object StatusCode
Invoke-WebRequest http://localhost:8080/team1f25-jupyter/ -UseBasicParsing | Select-Object StatusCode

# stop/remove when done
./apache-local/stop-proxy.ps1
```

## Git Bash usage

Important: Prevent MSYS from mangling Windows paths by setting `MSYS_NO_PATHCONV=1` for the docker command.

```bash
# from repo root
img=httpd:2.4; docker pull "$img"
export MSYS_NO_PATHCONV=1

# or simply use the helper script (optional port):
./apache-local/start-proxy.sh 8080

# check logs
docker logs --tail 80 "$cid"

# test
curl -I http://localhost:8080/team1f25/
curl -I http://localhost:8080/team1f25-jupyter/

# stop/remove when done
./apache-local/stop-proxy.sh
```

## Notes
- If you see 404s, ensure the volumes mounted correctly inside the container.
- WebSockets are enabled via `mod_proxy_wstunnel` and rewrite rules.
- For HTTPS testing locally, you could front this with an mkcert-generated cert or use a different local setup; HTTP is sufficient for functional checks.
