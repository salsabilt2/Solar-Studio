"""Run the 40-question document-grounding evaluation against a configured instance."""

import json
import os
import time
from io import BytesIO
from pathlib import Path

import httpx
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

QUESTIONS = json.loads((Path(__file__).parent / "questions.json").read_text())
FACTS = [
    "Synthetic evaluation facts. These are a controlled test fixture, not manufacturer documents.",
    "JinkoSolar test panel: rated power 440 watts; length 1762 mm; width 1134 mm; area 1.998 square metres; temperature coefficient -0.29 percent per Celsius degree.",
    "AIKO test panel: rated power 455 watts; length 1757 mm; width 1134 mm; area 1.992 square metres; temperature coefficient -0.26 percent per Celsius degree.",
    "Qcells test panel: rated power 440 watts; length 1722 mm; width 1134 mm; area 1.953 square metres; temperature coefficient -0.30 percent per Celsius degree.",
]


def fixture_pdf() -> bytes:
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    text = pdf.beginText(40, A4[1] - 50)
    text.setFont("Helvetica", 10)
    for line in FACTS:
        for word_group in [line[index : index + 95] for index in range(0, len(line), 95)]:
            text.textLine(word_group)
        text.textLine("")
    pdf.drawText(text)
    pdf.save()
    return output.getvalue()


def main() -> None:
    base = os.environ["SOLAR_EVAL_URL"].rstrip("/")
    with httpx.Client(base_url=base, timeout=60) as browser:
        login = browser.post(
            "/api/v1/auth/login",
            json={
                "email": os.environ["SOLAR_EVAL_EMAIL"],
                "password": os.environ["SOLAR_EVAL_PASSWORD"],
            },
        )
        login.raise_for_status()
        documents = browser.get("/api/v1/ai/documents")
        documents.raise_for_status()
        matching = [item for item in documents.json() if item["filename"] == "evaluation-facts.pdf"]
        if not matching:
            uploaded = browser.post(
                "/api/v1/ai/documents",
                files={
                    "file": ("evaluation-facts.pdf", fixture_pdf(), "application/pdf"),
                },
            )
            uploaded.raise_for_status()
            document = uploaded.json()
        else:
            document = matching[-1]
        if document["status"] == "failed":
            retry = browser.post(f"/api/v1/ai/documents/{document['id']}/retry")
            retry.raise_for_status()
        for _ in range(120):
            listed = browser.get("/api/v1/ai/documents")
            listed.raise_for_status()
            current = next(item for item in listed.json() if item["id"] == document["id"])
            if current["status"] == "ready":
                break
            if current["status"] == "failed":
                raise RuntimeError(current["error"] or "The evaluation PDF could not be indexed.")
            time.sleep(1)
        else:
            raise TimeoutError("The evaluation PDF did not finish indexing in two minutes.")
        rows = []
        for item in QUESTIONS:
            result = browser.post("/api/v1/ai/ask", json={"question": item["question"]})
            result.raise_for_status()
            payload = result.json()
            answer = payload["answer"] or ""
            cited = bool(payload["sources"])
            supported_pass = cited and all(term in answer.lower() for term in item.get("terms", []))
            unsupported_pass = not cited and any(
                phrase in answer.lower()
                for phrase in (
                    "do not",
                    "does not",
                    "cannot",
                    "not provided",
                    "not answer",
                    "no evidence",
                    "unsupported",
                )
            )
            rows.append(
                {
                    "question": item["question"],
                    "expected_supported": item["supported"],
                    "answer": answer,
                    "sources": payload["sources"],
                    "passed": supported_pass if item["supported"] else unsupported_pass,
                }
            )
    results = {
        "total": len(rows),
        "passed": sum(row["passed"] for row in rows),
        "supported_passed": sum(row["passed"] for row in rows if row["expected_supported"]),
        "unsupported_passed": sum(row["passed"] for row in rows if not row["expected_supported"]),
        "failures": [row for row in rows if not row["passed"]],
        "details": rows,
    }
    target = Path(__file__).parent / "results.json"
    target.write_text(json.dumps(results, indent=2))
    print(f"{results['passed']}/{results['total']} passed; details: {target}")


if __name__ == "__main__":
    main()
