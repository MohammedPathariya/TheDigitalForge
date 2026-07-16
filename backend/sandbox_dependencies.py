"""Pinned third-party capabilities available inside offline sandboxes."""

SANDBOX_PACKAGES = (
    "chromadb==1.1.1",
    "email-validator==2.3.0",
    "fastapi==0.139.0",
    "httpx==0.28.1",
    "modal==1.5.1",
    "openai==2.45.0",
    "pydantic==2.12.5",
    "pydantic-settings==2.10.1",
    "pytest==9.1.1",
    "starlette==1.3.1",
)

SUPPORTED_SANDBOX_IMPORTS = frozenset(
    {
        "chromadb",
        "email_validator",
        "fastapi",
        "httpx",
        "modal",
        "openai",
        "pydantic",
        "pydantic_settings",
        "pytest",
        "starlette",
    }
)

SANDBOX_CAPABILITY_SUMMARY = ", ".join(SANDBOX_PACKAGES)
