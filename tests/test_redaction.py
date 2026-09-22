from app.observability.logger import (
    redact_dict,
    redact_text,
)


def test_password_is_redacted():
    data = {
        "username": "demo-user",
        "password": "secret123",
    }

    result = redact_dict(data)

    assert result["username"] == "demo-user"
    assert result["password"] == "[REDACTED]"


def test_api_key_is_redacted():
    data = {
        "api_key": "sk-example-secret-key",
    }

    result = redact_dict(data)

    assert result["api_key"] == "[REDACTED]"


def test_token_is_redacted():
    data = {
        "token": "example-token-value",
    }

    result = redact_dict(data)

    assert result["token"] == "[REDACTED]"


def test_authorization_is_redacted():
    data = {
        "authorization": "Bearer example-token",
    }

    result = redact_dict(data)

    assert result["authorization"] == "[REDACTED]"


def test_nested_secret_is_redacted():
    data = {
        "request": {
            "member": "demo-member",
            "credential": "private-value",
        }
    }

    result = redact_dict(data)

    assert (
        result["request"]["credential"]
        == "[REDACTED]"
    )

    assert (
        result["request"]["member"]
        == "demo-member"
    )


def test_secret_inside_list_is_redacted():
    data = {
        "events": [
            {
                "action": "login",
                "access_token": "secret-token",
            }
        ]
    }

    result = redact_dict(data)

    assert (
        result["events"][0]["access_token"]
        == "[REDACTED]"
    )


def test_password_in_text_is_redacted():
    text = "password=super-secret-value"

    result = redact_text(text)

    assert "super-secret-value" not in result
    assert "[REDACTED]" in result


def test_api_key_in_text_is_redacted():
    text = "api_key=sk-example-secret"

    result = redact_text(text)

    assert "sk-example-secret" not in result
    assert "[REDACTED]" in result