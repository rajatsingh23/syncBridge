import hashlib 
import hmac

def generate_signature(payload: bytes, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

def verify_signature(
        payload: bytes,
        signature: str,
        secret: str,
) -> bool:
    expected_signature = generate_signature(
        payload=payload,
        secret=secret,
    )

    return hmac.compare_digest(
        expected_signature,
        signature,
    )