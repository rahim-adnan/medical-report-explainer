# backend/report_analyzer.py
"""
Report Analyzer — sends extracted PDF text to LLaMA 3 via Groq
and returns a richly structured analysis of the medical report.

The analysis is broken into clear sections:
  • summary          — plain-English overview (2–3 sentences)
  • findings         — list of individual test results with status
  • abnormal_flags   — only the out-of-range results, highlighted
  • doctor_questions — smart questions the patient should ask
  • lifestyle_tips   — actionable non-medical suggestions
  • disclaimer       — mandatory safety notice
"""

import json
import re
from groq import Groq


class ReportAnalyzer:
    """
    Analyzes medical report text using LLaMA 3 via Groq API.

    Usage:
        analyzer = ReportAnalyzer(api_key)
        result   = analyzer.analyze(report_text, language="English")
    """

    MODEL = "llama-3.3-70b-versatile"

    SYSTEM_PROMPT = """You are MedExplain AI — a compassionate, highly accurate medical report interpreter.

Your role is to help patients understand their medical reports in plain language.
You are NOT a doctor. You NEVER diagnose. You NEVER prescribe. You NEVER give medical advice.
You explain what the numbers mean, flag what's outside normal range, and help patients
formulate smart questions for their actual doctor.

You respond ONLY with valid JSON — no preamble, no markdown fences, no extra text.

Your JSON must follow this exact schema:
{
  "summary": "2-3 sentence plain-English overview of the report",
  "report_type": "e.g. Complete Blood Count, Lipid Panel, Liver Function Test, etc.",
  "overall_status": "normal | attention_needed | urgent",
  "findings": [
    {
      "name": "Test name",
      "value": "measured value with unit",
      "reference_range": "normal range",
      "status": "normal | low | high | critical",
      "explanation": "What this test measures in 1 simple sentence",
      "what_it_means": "What this specific result means for this patient"
    }
  ],
  "abnormal_flags": [
    {
      "name": "Test name",
      "value": "measured value",
      "status": "low | high | critical",
      "simple_explanation": "In plain English, why this matters"
    }
  ],
  "doctor_questions": [
    "Smart question 1 the patient should ask their doctor",
    "Smart question 2",
    "Smart question 3",
    "Smart question 4",
    "Smart question 5"
  ],
  "lifestyle_tips": [
    {
      "tip": "Actionable general wellness tip",
      "reason": "Why this is relevant to this report"
    }
  ],
  "disclaimer": "This analysis is for educational purposes only and does not constitute medical advice. Always consult a qualified healthcare professional for diagnosis and treatment."
}

Rules:
- Use simple language a 16-year-old can understand
- Never use medical jargon without immediately explaining it
- Be compassionate and reassuring, not alarming
- If a value is critical, be honest but calm
- If report text is unclear or incomplete, still do your best and note uncertainty in the summary
- Always include the disclaimer exactly as shown
"""

    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    # ── Public API ─────────────────────────────────────────────────────────────
    def analyze(self, report_text: str, language: str = "English") -> dict:
        """
        Sends report text to LLaMA 3 and returns structured analysis dict.
        Raises ValueError if the LLM response cannot be parsed.
        """
        prompt = self._build_prompt(report_text, language)
        raw = self._call_llm(prompt)
        return self._parse_response(raw)

    # ── Internal helpers ───────────────────────────────────────────────────────
    def _build_prompt(self, report_text: str, language: str) -> str:
        lang_note = f"\n\nIMPORTANT: Respond in {language} language." if language != "English" else ""
        return f"""Please analyze this medical report and return a JSON response following the schema exactly.{lang_note}

--- MEDICAL REPORT START ---
{report_text}
--- MEDICAL REPORT END ---

Return ONLY valid JSON. No markdown, no explanation outside the JSON."""

    def _call_llm(self, prompt: str) -> str:
        """Calls Groq API and returns raw response string."""
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.2,      # Low temp = more consistent, accurate output
            max_tokens=4096,
        )
        return response.choices[0].message.content.strip()

    def _parse_response(self, raw: str) -> dict:
        """
        Robustly parses the LLM JSON response.
        Strips markdown fences if the model added them despite instructions.
        """
        # Strip ```json ... ``` fences if present
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}\nRaw response: {raw[:500]}")
