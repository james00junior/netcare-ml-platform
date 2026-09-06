"""Security regression tests for credential handling and privacy-safe configuration."""

from pydantic import SecretStr

from src.config.settings import Settings


def test_databricks_serving_token_is_secret_value() -> None:
    settings = Settings(DATABRICKS_SERVING_TOKEN="test-token")

    assert isinstance(settings.databricks_serving_token, SecretStr)
    assert settings.databricks_serving_token.get_secret_value() == "test-token"
    assert str(settings.databricks_serving_token) == "**********"


def test_api_key_is_secret_value() -> None:
    settings = Settings(API_KEY="test-api-key")

    assert isinstance(settings.api_key, SecretStr)
    assert settings.api_key.get_secret_value() == "test-api-key"
    assert str(settings.api_key) == "**********"


def test_secret_values_are_not_configured_by_default() -> None:
    settings = Settings(_env_file=None)

    assert settings.databricks_serving_token is None
    assert settings.api_key is None


def test_production_identity_configuration_does_not_require_pat() -> None:
    settings = Settings(
        ENV="prod",
        DATABRICKS_SERVING_ENDPOINT="https://example.databricks.com/serving-endpoints/test/invocations",
    )

    assert settings.is_production is True
    assert settings.databricks_serving_token is None
