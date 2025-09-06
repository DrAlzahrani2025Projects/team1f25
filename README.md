# Team1 Proxy + App + Jupyter

This project uses **Docker Compose** to run:

- **Apache HTTPD** as a reverse proxy  
- **Team1 App** (Flask + Gunicorn) serving “Hello, World!”  
- **JupyterLab** environment, proxied behind Apache  

---

## 🔧 Requirements

- [Docker](https://docs.docker.com/get-docker/)  
- [Docker Compose](https://docs.docker.com/compose/install/)  

---

## ▶️ Setup

To build and start everything:

```bash
./docker-setup.sh
```

This will:

- Stop any existing containers  
- Rebuild images  
- Start all services in the background  

When it finishes, you’ll see URLs like:

- Team1 App → [http://localhost:2501/team1/](http://localhost:2501/team1/)  
- Team1 Jupyter → [http://localhost:2501/team1/jupyter/](http://localhost:2501/team1/jupyter/)  

> 🔐 Note: Jupyter is configured **without a token/password**, only accessible through the proxy on port `2501`.

---

## 🛑 Cleanup

To stop and remove containers, networks, and orphans:

```bash
./docker-cleanup.sh
```

---

## 📂 Project Structure

```
.
├── apache/
│   ├── httpd.conf          # Base Apache config
│   └── team1.conf          # VirtualHost & proxy rules
├── team1-app/
│   ├── Dockerfile          # Builds the Flask app container
│   └── app.py              # Hello World app
├── team1-notebooks/        # Jupyter working directory (mounted)
├── docker-compose.yml      # Service definitions
├── docker-setup.sh         # Setup helper script
└── docker-cleanup.sh       # Cleanup helper script
```

---

## ⚙️ Useful Commands

- See logs:
  ```bash
  docker-compose logs -f
  ```

- Restart just the proxy:
  ```bash
  docker-compose restart proxy
  ```

- Rebuild only the app:
  ```bash
  docker-compose up -d --build team1-app
  ```

---

## ✅ Health Check

The Team1 app exposes a health endpoint:

```bash
curl http://localhost:2501/team1/health
# -> {"ok": true}
```

---

Happy coding 🎉
