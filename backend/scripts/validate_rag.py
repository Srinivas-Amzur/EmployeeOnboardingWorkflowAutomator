import asyncio
from pathlib import Path

from httpx import AsyncClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.api.dependencies import get_current_user
from app.core.security import TokenData
from app.main import create_app


def build_pdf(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    lines = [
        "Employee Onboarding Handbook",
        "The onboarding process has five states: initiated, hr_review, provisioning, meetings_scheduled, documents_shared.",
        "VPN setup policy: install corporate VPN client, enable MFA, and verify secure access before day one.",
        "HR policy: NDA and compliance documents must be acknowledged during onboarding.",
        "Employees should complete orientation and manager introduction in the first week.",
    ]
    y = 760
    for line in lines:
        c.drawString(72, y, line)
        y -= 22
    c.save()


async def main() -> None:
    app = create_app()

    def override_user() -> TokenData:
        return TokenData(
            sub="11111111-1111-1111-1111-111111111111",
            email="qa.assistant@company.com",
            role="admin",
            exp="2099-01-01T00:00:00+00:00",
        )

    app.dependency_overrides[get_current_user] = override_user

    temp_pdf = Path("./uploads/test_onboarding_validation.pdf")
    temp_pdf.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(temp_pdf)
    pdf_bytes = temp_pdf.read_bytes()

    async with AsyncClient(app=app, base_url="http://test") as client:
        upload = await client.post(
            "/api/v1/rag/documents/upload",
            files={"file": (temp_pdf.name, pdf_bytes, "application/pdf")},
            data={"document_type": "onboarding_policy"},
        )

        question_one = await client.post(
            "/api/v1/rag/chat",
            json={"question": "What does the VPN setup policy require?", "top_k": 5},
        )
        question_two = await client.post(
            "/api/v1/rag/chat",
            json={
                "question": "Summarize the onboarding workflow states.",
                "top_k": 5,
                "session_id": question_one.json().get("session_id"),
            },
        )
        search = await client.post(
            "/api/v1/rag/search",
            json={"query": "NDA compliance documents", "top_k": 3},
        )

    print("UPLOAD_STATUS", upload.status_code)
    print("UPLOAD_CHUNKS", upload.json().get("chunks_indexed"))
    print("Q1_STATUS", question_one.status_code)
    print("Q1_ANSWER", question_one.json().get("answer", "")[:220])
    print("Q1_SOURCES", len(question_one.json().get("sources", [])))
    print("Q2_STATUS", question_two.status_code)
    print("Q2_ANSWER", question_two.json().get("answer", "")[:220])
    print("Q2_SOURCES", len(question_two.json().get("sources", [])))
    print("SEARCH_STATUS", search.status_code)
    print("SEARCH_HITS", len(search.json()))
    if search.json():
        print("TOP_HIT_DOC", search.json()[0].get("document_name"))
        print("TOP_HIT_SCORE", search.json()[0].get("score"))


if __name__ == "__main__":
    asyncio.run(main())
