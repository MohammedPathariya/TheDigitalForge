# Pydantic Settings

## Environment-backed settings

Subclass `pydantic_settings.BaseSettings` to define typed application configuration.
Fields not supplied as initializer keyword arguments are resolved from configured settings
sources such as environment variables, while explicit initializer values can override
them in tests.

## Dotenv configuration

Set `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")`
to load dotenv values. `env_prefix` applies a prefix to environment variable names.
Environment variables take priority over dotenv values, and field defaults remain the
fallback when no configured source supplies a value.
