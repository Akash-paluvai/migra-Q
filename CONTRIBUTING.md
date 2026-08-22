# Contributing to Migra-Q

Thank you for your interest in contributing to Migra-Q! We welcome contributions from the community to help us build the most robust, deterministically verified SQL migration platform available.

## Getting Started

1. Familiarize yourself with the project by reading the documentation in `docs/`, particularly:
   - `ARCHITECTURE.md` (The 9-Phase Pipeline)
   - `APPROACH.md` (Why deterministic validation is preferred over LLM assertions)
   - `TERMINOLOGY.md` (Glossary of domain terms)
   - `VALIDATION.md` (How the deterministic validation engine works)
2. Follow the setup instructions in `DEVELOPMENT.md` to get your local environment running.

## Development Workflow

1. Fork the repository and create your branch from `main`.
2. Ensure you have the required environment variables (`.env`) for local sandbox testing.
3. Write your code, ensuring you follow the project's architecture and terminology conventions.
4. Run the test suites:
   ```bash
   pytest tests/
   ```
5. Ensure the frontend passes type checking and linting (if applicable).

## Pull Request Guidelines

When submitting a Pull Request (PR), please adhere to the following guidelines:

- **Descriptive Title**: Clearly state the purpose of the PR (e.g., `fix: Resolve dataset resolution bug in Schema Preflight`).
- **Detailed Description**: Explain *what* changes were made and *why*. If your PR fixes a specific issue, link to it.
- **Testing**: All new features and bug fixes must include corresponding tests. Do not submit a PR without tests if it modifies execution, validation, or orchestration logic.
- **Isolation**: Ensure your tests do not pollute `migraq.db` outside of test transactions.
- **Pass CI**: Ensure all automated checks (Pytest, linting) pass before requesting a review.

## Code Style

- **Python**: We follow standard Python stylistic conventions. Please ensure your code is clean, readable, and properly typed.
- **TypeScript/React**: Follow the established patterns in the `frontend/` directory.

## Reporting Issues

If you encounter a bug or have a feature request, please open an issue using the templates provided (if available) or include the following information:
- A clear and descriptive title.
- Steps to reproduce the issue.
- Expected behavior vs actual behavior.
- Relevant logs or error messages (particularly from the Execution or Validation phases).

By contributing to Migra-Q, you agree to abide by the terms of the project's [LICENSE](../LICENSE).
