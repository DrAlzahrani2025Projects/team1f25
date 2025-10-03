## Prerequisites

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

### Step 5: Build the docker image:

Run the command to build Docker container:

```
docker build -t team1f25-streamlit:latest .
```

### Step 6: Run the container:

```
docker run -d -p 5001:5001 --name team1f25 team1f25-streamlit:latest streamlit run app.py --server.port=5001 --server.address=0.0.0.0 --server.enableCORS=false --server.baseUrlPath=/team1f25
```

If you're using git bash run the below command

```
docker run -d -p 5001:5001 --name team1f25 team1f25-streamlit:latest
```
### Optional Step : Error: port is already allocated

If you're encountering error: port is already allocated 

```
docker stop $(docker ps -q --filter "publish=5001")
docker ps -a -q | xargs -r docker rm
```

then run step 5 and 6 again

### Step 7: Access AI Agent

For Streamlit:

- Once the container starts, Open browser at http://localhost:5001/team1f25
  

---

### Hosted on CSE department web server

For Streamlit:

Open browser at https://sec.cse.csusb.edu/team1f25/

## Google Colab Notebook  

We have integrated a Google Colab notebook for easy access and execution.

[Open in Colab](https://colab.research.google.com/drive/1tf7gLr7rv-YE5rZq6R0iJzA3-MUVs38N?usp=sharing)

