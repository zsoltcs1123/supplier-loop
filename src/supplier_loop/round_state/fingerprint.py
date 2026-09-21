from supplier_loop.simulator.port import EmailMessage


def quote_fingerprint(message: EmailMessage) -> str:
    return f"{message.from_address.casefold()}|{message.subject}"
