# Security Policy

## Secrets

Do not commit `config.json`, `.env` files, API keys, local documents, logs, or
search indexes. Use `config.example.json` as the template and keep private
values in your local `config.json` or environment variables.

Smart Rename reads `NVIDIA_API_KEY` from the environment or
`smart_rename.api_key` from a local `config.json`.

## Data leaving your machine

Only Smart Rename sends text externally (the first ~600 characters of each document, to
the NVIDIA API) and only when enabled. Dry runs never call it. The search cache is JSON,
not pickle.

## Reporting a vulnerability

Please open a private security advisory on GitHub or contact the maintainer
privately. Include reproduction steps, impact, affected versions or commits,
and any suggested mitigation.
