
*Team 1F25 – Scholar AI Assistant*

---

## Introduction
This guide explains how to set up and run the Scholar Assistant AI project using *Docker*.  
Docker allows you to run applications inside lightweight, isolated environments called *containers*, ensuring consistency across different machines.

---

## Prerequisites
Before starting, make sure the following software is installed on your system:

| Software | Description | Download Link |
|-----------|--------------|----------------|
| Docker Desktop | A platform for building, running, and managing containers. | [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) |
| Git | A version control system used to clone and manage repositories. | [https://git-scm.com/downloads](https://git-scm.com/downloads) |

Verify Docker installation:
```bash
docker --version
```
This command should display your Docker version, confirming it’s installed correctly.

---
git clone https://github.com/DrAlzahrani2025Projects/team1f25.git
```
*Definition:*  
Cloning a repository means creating a local copy of the project on your computer.

---

### Step 2: Navigate to the team1f25 project
Move into the project:
```bash
cd team1f25
```
*Definition:*  
cd (change directory) is a command used to move between folders in your terminal.

---

### Step 3: Build the Docker Image
Create a Docker image (a blueprint of your app) from the Dockerfile:
```bash
docker build -f docker/Dockerfile -t team1f25-streamlit .
```
*Definition:*  
A *Docker image* is a packaged version of your application, including all dependencies, that can be used to create containers.

---

### Step 4: Run the Container
Start your app inside a container using:
```bash
docker run -p 5001:5001 -e GROQ_API_KEY="your-key" --name team1f25 team1f25-streamlit
```
*Definition:*  
A *container* is a running instance of an image.  
Explanation of command flags:
- -p 5001:5001 — Maps port 5001 on your machine to port 5001 in the container.  
- -e GROQ_API_KEY="your-key" — Passes your API key as an environment variable.  
- --name team1f25 — Names your container “team1f25”.

---

### Step 5: Open the App
Once the container is running, open your browser and visit:
```bash
http://localhost:5001/team1f25
```
Your Scholar Assistant AI application should now be running.

---

## Summary

| Step | Action | Command |
|------|---------|----------|
| 1 | Clone the repository | git clone https://github.com/DrAlzahrani2025Projects/team1f25.git |
| 2 | Navigate to folder | cd team1f25 |
| 3 | Build Docker image | docker build -f docker/Dockerfile -t team1f25-streamlit . |
| 4 | Run the container | docker run -p 5001:5001 -e GROQ_API_KEY="your-key" --name team1f25 team1f25-streamlit |
| 5 | Open in browser | http://localhost:5001/team1f25 |
