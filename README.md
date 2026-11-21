# Samjho AI

Explains rent, loan and insurance documents in simple English or Hindi for first-time users in India.

**Flow:** upload photo/PDF -> OCR -> mask personal data (Aadhaar, PAN, phone, email, account) -> rules engine decides the verdict -> local LLM explains in simple words. Nothing is stored.

## Project layout
```
samjho-ai/
├── main.py            web server (FastAPI)
├── rules.py           masking, document detection, rules, verdict
├── test_rules.py      tests for rules.py
├── requirements.txt
└── static/            index.html, app.js, style.css
```

## Run locally
1. Install Tesseract (with Hindi), Poppler and Ollama
   - Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-hin poppler-utils`
2. `ollama pull qwen2.5:7b` (use `qwen2.5:3b` on a weaker laptop and set `OLLAMA_MODEL`)
3. `pip install -r requirements.txt`
4. `python test_rules.py`
5. `uvicorn main:app --port 8000` and open http://localhost:8000

## Environment variables
- `OLLAMA_URL` (default `http://localhost:11434`)
- `OLLAMA_MODEL` (default `qwen2.5:7b`)
- `ALLOWED_ORIGINS` (default `http://localhost:8000`)

## Disclaimer
This is a reading aid, not legal advice. Thresholds in `rules.py` (30% rent, 40% EMI, 10x cover, 2-month deposit) are guidelines and need review by a lawyer or CA.
