# Security Policy

## Secrets

Do not commit `config.json`, `.env` files, API keys, local documents, logs, or
search indexes. Use `config.example.json` as the template and keep private
values in your local `config.json` or environment variables.

Smart Rename reads `NVIDIA_API_KEY` from the environment or
`smart_rename.api_key` from a local `config.json`.

## Reporting a vulnerability

Please open a private security advisory on GitHub or contact the maintainer
privately. Include reproduction steps, impact, affected versions or commits,
and any suggested mitigation.
