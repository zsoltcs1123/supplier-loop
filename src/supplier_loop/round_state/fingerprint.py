import hashlib

from supplier_loop.simulator.port import EmailMessage


def quote_fingerprint(message: EmailMessage) -> str:
    attachments = ",".join(sorted(message.attachment_ids))
    payload = "\n".join(
        [message.from_address.casefold(), message.subject, message.body, attachments]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
