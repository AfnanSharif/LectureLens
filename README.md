<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=f857a6,ff5858&height=200&section=header&text=LectureLens&fontSize=70&fontColor=ffffff&animation=twinkling" width="100%" />

<img src="https://img.icons8.com/?id=44010&format=png&size=100" width="90" />

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=22&duration=2500&pause=1000&color=f857a6&center=true&vCenter=true&width=700&height=50&lines=Educational%20video%20summaries%2C%20quizzes%2C%20and%20feedback;Python%20+%20Flask" alt="Typing SVG" />

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Flask](https://img.shields.io/badge/Flask-API-000000?style=for-the-badge&logo=flask&logoColor=white)](#)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](#)
[![Whisper](https://img.shields.io/badge/Whisper-412991?style=for-the-badge)](#)

</div>

---

## 📖 Overview

**LectureLens** — Educational video summaries, quizzes, and feedback.

Core logic lives in `src/video_summarizer/`. Configuration is centralized in `config/settings.yaml`
and secrets/API keys are loaded from a local `.env` (see `.env.example`).

## 🏗️ Project Layout

```
LectureLens/
├── app.py               # Flask entry point
├── src/video_summarizer/
│   └── ...              # Core package — educational video summaries, quizzes, and feedback
├── config/settings.yaml # App configuration
├── tests/                # Unit tests
├── scripts/setup.sh      # venv + install helper (macOS/Linux)
├── requirements.txt
```

### Also included
- `Dockerfile` — containerized deployment


## ⚡ Setup & Run

### 🪟 Windows (PowerShell / CMD)
```cmd
git clone https://github.com/AfnanSharif/LectureLens.git
cd LectureLens

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
:: edit .env to add any API keys — the app runs fully offline without them

python app.py
```

### 🍎 macOS / 🐧 Linux
```bash
git clone https://github.com/AfnanSharif/LectureLens.git
cd LectureLens

./scripts/setup.sh                 # creates .venv and installs requirements.txt
source .venv/bin/activate

cp .env.example .env
# edit .env to add any API keys — the app runs fully offline without them

python app.py
```

Open **http://localhost:5000**.

```bash
make test    # run the test suite
make lint    # lint the codebase
```

---

<div align="center">

**Created by [AfnanSharif](https://github.com/AfnanSharif)** · ⭐ star this repo if it helped you

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=f857a6,ff5858&height=80&section=footer" width="100%" />

</div>
