import secrets

def generate_otp(length: int = 6) -> str:
    import random  # moved inside to avoid circular import issues
    digits = "0123456789"
    return "".join(random.choice(digits) for _ in range(length))