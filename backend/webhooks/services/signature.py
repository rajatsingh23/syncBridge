import base64
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


def generate_shopify_signature(
    payload: bytes,
    secret: str,
) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).digest()

    return base64.b64encode(digest).decode("utf-8")


def verify_shopify_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    expected_signature = generate_shopify_signature(
        payload=payload,
        secret=secret,
    )

    return hmac.compare_digest(
        expected_signature,
        signature,
    )

def generate_woocommerce_signature(
    payload: bytes,
    secret: str,
) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).digest()

    return base64.b64encode(digest).decode("utf-8")


def verify_woocommerce_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    expected_signature = generate_woocommerce_signature(
        payload=payload,
        secret=secret,
    )

    return hmac.compare_digest(
        expected_signature,
        signature,
    )