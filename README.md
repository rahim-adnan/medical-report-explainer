# MedExplain AI 🏥

> Upload any medical report PDF — get a clear, plain-English explanation powered by LLaMA 3.

**[Demo Video](YOUR_YOUTUBE_URL_HERE)**

---

## What it does

Most people receive medical reports full of numbers and abbreviations they don't understand. MedExplain AI bridges that gap:

- 📄 **Upload** any blood test, lab panel, or medical report PDF
- 🧠 **AI analyzes** every value against reference ranges using LLaMA 3
- 🚦 **Flags** what's normal, low, high, or critical — color-coded at a glance
- 💬 **Generates** smart questions to ask your doctor
- 🌱 **Suggests** actionable wellness tips relevant to your results
- 🌍 **Responds in 7 languages** — English, Hungarian, German, French, Spanish, Arabic, Turkish

---

## Tech Stack

| Layer     | Technology |
|-----------|-----------|
| Backend   | Python · Flask |
| AI        | LLaMA 3 70B via Groq API (free) |
| PDF       | PyMuPDF (fitz) |
| Frontend  | Vanilla HTML · CSS · JavaScript |

---

## Project Structure

```
medical_report_explainer/
├── backend/
│   ├── app.py              # Flask app — routes and API
│   ├── pdf_parser.py       # PDF text extraction + cleaning
│   └── report_analyzer.py  # LLM analysis via Groq
├── frontend/
│   ├── templates/
│   │   └── index.html      # Main HTML
│   └── static/
│       ├── css/style.css   # Full stylesheet
│       └── js/app.js       # Frontend logic
├── requirements.txt
└── .env.example
```

---

## Local Setup

### 1. Clone and install

```bash
git clone https://github.com/rahim-adnan/medical-report-explainer
cd medical-report-explainer
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Get a free Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Create an API key

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 4. Run

```bash
cd backend
python app.py
```

Open [http://localhost:5000](http://localhost:5000)

---

## Important Disclaimer

> This application is for **educational purposes only**. It does not constitute medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for medical decisions.

---

*Built by [Adnan Rahim](https://github.com/rahim-adnan) · Powered by LLaMA 3 via Groq*
