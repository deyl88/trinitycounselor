# Trinity Counselor — Phase 0 Prototype

Single-partner counselor proving the core loop before multi-agent complexity.

## Setup

```bash
pip install anthropic fastapi uvicorn python-dotenv
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
uvicorn main:app --reload
```

## What this proves
- Persistent therapeutic conversation with rolling summary compression
- Theme extraction from private content (SAP layer prototype)
- Counselor persona consistency across sessions
