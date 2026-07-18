from uuid import uuid4

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_round_trip() -> None:
    encoded = hash_password("correct-horse-battery-staple")
    assert encoded != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", encoded)
    assert not verify_password("wrong-password", encoded)


def test_signed_access_token_round_trip_and_tamper_rejection() -> None:
    user_id = uuid4()
    token = create_access_token(user_id)
    assert decode_access_token(token) == user_id
    body, signature = token.split(".")
    replacement = "A" if signature[-1] != "A" else "B"
    assert decode_access_token(f"{body}.{signature[:-1]}{replacement}") is None
