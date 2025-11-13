# Scholar AI Assistant — User Guide

Your conversational research companion for discovering academic resources from the CSUSB library. This guide covers installation, configuration, running with Docker, and how to use the chat experience effectively.


## What it is

- A Streamlit web app that chats with you to clarify your research needs, then searches the CSUSB Primo library database and presents results in a clean table with direct links.
- Powered by the Groq LLM (you will need a GROQ API key).


## Key features

- Natural chat to refine topic, resource type (articles, books, journals, theses), and number of results
- Smart date handling (e.g., "last 5 years", "since 2019", or concrete ranges like 2018–2022)
- Results table with title, authors, year, type, and a link to the full record in Primo
- Suggestions when no results are found


## Prerequisites

This guide focuses on running the app with Docker:

- Docker Desktop
- A Groq API key (environment variable GROQ_API_KEY)
- On Windows, WSL2 is recommended for Docker integration


## Run with Docker

The repo includes a production-friendly Dockerfile that sets a base URL path for easy reverse-proxying.

- Build and run (PowerShell)

```powershell
# From the repo root
docker build -f docker/Dockerfile -t team1f25-streamlit .

docker run -d `
  -p 5001:5001 `
  -e GROQ_API_KEY="YOUR_GROQ_API_KEY" `
  --name team1f25 `
  team1f25-streamlit
```

- Open the app at: http://localhost:5001/team1f25

- Stop and remove the container later

```powershell
docker stop team1f25
docker rm team1f25
```

- Optional cleanup of image

```powershell
docker rmi team1f25-streamlit
```

If you prefer using the provided bash scripts (Linux/macOS or Windows via WSL/Git Bash):
- scripts/startup.sh builds and runs the container after prompting for your Groq API key
- scripts/cleanup.sh stops/removes the container and image (use --hard to also purge ./data)


## Using the app

1) Open the app in your browser
- Docker: http://localhost:5001/team1f25

2) Start chatting
- Describe your research topic in natural language
- The assistant will ask focused follow-ups if needed
- Say “search now” to trigger an immediate search

3) Pick resource type and scope
- You can specify: articles, books, journals, or theses
- You can limit the number of results (e.g., "I need 5 articles")

4) Add date constraints (optional)
- Examples it understands:
  - “last 5 years”
  - “since 2019”
  - “2015-2018”
  - “March 2020” or “2020-03-15”
  - “Q1 2018”
- Or say “any time” to ignore date filtering

5) Review results
- Results appear in a table with Title, Authors, Year, Type, and a 🔗 link to the Primo full record
- If nothing is found, the assistant suggests alternative broader searches


## Tips for better results

- Be specific: “machine learning in healthcare for diagnosis” beats “AI”
- Choose a resource type: “journal articles” maps to articles; “journals” means journal publications
- Use a reasonable result count: 5–20 usually works best
- Use time filters when timeliness matters (e.g., cybersecurity in the last 3 years)


## Troubleshooting

- “Please set your GROQ_API_KEY…”
  - Ensure you pass your key via `-e GROQ_API_KEY="..."` when running `docker run` (or use `scripts/startup.sh`).
- Docker port already in use (0.0.0.0:5001)
  - Stop whatever is using that port or change the -p mapping
- No results found
  - Try a broader query, remove strict resource/date filters, or use the suggestions shown
- Primo API/network errors
  - Check your internet connection and try again; the client uses retries for transient errors


## Advanced configuration

These environment variables tune behavior:

- GROQ_MODEL: default `llama-3.3-70b-versatile`

Pass them as `-e` flags to `docker run`, for example:

```powershell
docker run -d `
  -p 5001:5001 `
  -e GROQ_API_KEY="YOUR_GROQ_API_KEY" `
  --name team1f25 `
  team1f25-streamlit
```


## Where else is it available?

- Hosted (CSUSB): https://sec.cse.csusb.edu/team1f25/
- Google Colab notebook: https://colab.research.google.com/drive/1tf7gLr7rv-YE5rZq6R0iJzA3-MUVs38N?usp=sharing


## Uninstall/cleanup

- Docker (PowerShell):

```powershell
docker stop team1f25
docker rm team1f25
# optional
docker rmi team1f25-streamlit
```


## FAQ

- What data leaves my machine?
  - Your prompts go to Groq for LLM responses and the app queries the CSUSB Primo API for search results.
- Does it support REST APIs for external callers?
  - No, it’s a Streamlit UI app. Use the app interactively in a browser.
- Can I change the number of results?
  - Yes, just say it in chat (e.g., “show 5 articles”)—default is 10 if unspecified.
- Can I filter by resource type?
  - Yes: “articles”, “books”, “journals”, or “theses”.


---

If you run into issues not covered here, please open an issue on the repository or include your error message when asking for help.
