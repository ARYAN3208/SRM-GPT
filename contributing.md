# Contributing

Thank you for contributing.

## Setup

Install dependencies

```bash
pip install -r requirements.txt
```

Configure

- Python 3.10+
- Environment variables in `.env`

Run backend

```bash
python backend/server.py
```

---

## Project Structure

frontend/
UI only.

backend/
API server.

app/
Core application.

---

## Coding Style

- Follow existing architecture.
- Keep functions focused.
- Prefer readable code.
- Use type hints.
- Add docstrings where appropriate.
- Reuse existing utilities.

---

## Pull Requests

Before submitting:

- Ensure code runs.
- Run relevant tests.
- Avoid unrelated changes.
- Update documentation if needed.

---

## Commit Messages

Use conventional commits.

Examples

feat:

fix:

refactor:

docs:

test:

chore:

---

## Review Checklist

- Code is readable.
- No duplicated logic.
- Existing functionality preserved.
- No unnecessary dependencies.
- Tests pass.
- Documentation updated where needed.