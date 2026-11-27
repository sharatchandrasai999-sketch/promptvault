# Contributing

Thanks for helping. Version prompts on disk and A/B test them with a deterministic mock LLM. This is a small, personal project, so keep changes small and easy to review.

## Before you send a change

- Run the tests from any folder: `pytest -q` (tests must not depend on the current working directory)
- Keep the mock path working: `promptvault ab` must run offline with the built-in mock, no API key and no download.
- If you add a prompt command, ship an example prompt and test set with it, so a stranger can run it.

## Reporting a problem

Open an issue and include:

- The exact command you ran
- The input file, if it is about one
- What happened, and what you expected instead

Do not include API keys, private documents, or personal details.
