import uuid

def generate_ticket_code():
    return str(uuid.uuid4())[:8]