import json
from pathlib import Path

from supplier_loop.simulator.port import EmailMessage

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SAMPLE_EMAILS = _REPO_ROOT / "docs/fixtures/sample_traffic/emails"
_APPROVER_FIXTURE = (
    Path(__file__).resolve().parent / "mail_kind" / "fixtures" / "approver_ruling.json"
)


def email_from_json(path: Path) -> EmailMessage:
    data = json.loads(path.read_text(encoding="utf-8"))
    attachments = data.get("attachments") or []
    return EmailMessage(
        id=data["id"],
        from_address=data["from"],
        to_address=data["to"],
        subject=data["subject"],
        sim_time_hours=float(data["sim_time_hours"]),
        attachment_ids=list(attachments),
        body=data["body"],
    )


def load_sample_email(email_id: str) -> EmailMessage:
    for path in sorted(_SAMPLE_EMAILS.glob("*.json")):
        message = email_from_json(path)
        if message.id == email_id:
            return message
    raise KeyError(email_id)


def load_approver_ruling() -> EmailMessage:
    return email_from_json(_APPROVER_FIXTURE)


def sample_email_paths() -> list[Path]:
    return sorted(_SAMPLE_EMAILS.glob("*.json"))
