# WordQuest — English Word Guessing Game

A polished mini-project built with Python Flask, SQLite, HTML, CSS, and JavaScript.

## Features

- Three difficulty levels with 30 built-in words
- Two starter letters revealed, plus letter-by-letter guessing with keyboard support
- Helpful clues, limited attempts, scoring, and paid letter reveals
- SQLite game history and player progress dashboard
- Responsive, animated interface with sound feedback
- K.C. Dhanunjay Infosys footer banner with WhatsApp and website links
- Flask JSON API and server-side sessions

## Run locally

```powershell
cd english_word_guessing_project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

The database file `wordquest.db` is created automatically on first run.

## Deploy on Render

1. Create a new Blueprint in Render and connect this repository.
2. Render automatically reads the root-level `render.yaml` Blueprint file.
3. Render installs the dependencies, generates `SECRET_KEY`, and starts Gunicorn.

GitHub Actions automatically checks Python syntax, API behaviour, the health
endpoint, and the production Gunicorn command whenever this project changes.
"# word-guessing" 
