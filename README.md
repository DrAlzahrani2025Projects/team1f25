# Team1 Proxy + App + Jupyter

This project uses **Docker Compose** to run:

- **Apache HTTPD** as a reverse proxy  
- **Team1 App** (Flask + Gunicorn) serving “Hello, World!”  
- **JupyterLab** environment, proxied behind Apache  

---

## 🔧 Prerequisites

Before you begin, ensure you have the following:

1. **Git**: [Install Git](https://git-scm.com/) from its official website.
2. **Docker**: [Install Docker](https://www.docker.com) from its official website.
3. **Linux/MacOS**: No extra setup needed.
4. **Windows**: Install [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) and enable Docker's WSL integration by following [this guide](https://docs.docker.com/desktop/windows/wsl/).  

---

### Step 1: Remove the existing code directory completely

Because the local repository can't been updated correctly, need to remove the directory first.

```bash
rm -rf team1f25
```

### Step 2: Clone the Repository

Clone the GitHub repository to your local machine:

```
git clone https://github.com/DrAlzahrani2025Projects/team1f25.git
```

### Step 3: Navigate to the Repository

Change to the cloned repository directory:

```
cd team1f25
```

### Step 4: Pull the Latest Version

Update the repository to the latest version:

```
git pull origin main
```

### Step 5: Enable execute permissions for the Docker build and cleanup script:

Run the setup script to build and start the Docker container:

```
chmod +x docker-setup.sh
```

### ▶️ Setup

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

### Access the Chatbot

For Streamlit:

- Once the container starts, Open browser at 

### 🛑 Cleanup

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
