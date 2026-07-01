# Secure Assessment & Risk Management Platform

SARP is a portfolio MVP for fictional security assessment and risk management workflows.

## Day 1 Local Setup

```bash
cp .env.example .env
docker compose up --build -d
```

After the Django project files are implemented, run:

```bash
docker compose exec backend python manage.py makemigrations accounts
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_dev_users
docker compose exec backend python manage.py test apps.accounts
```

## Scope Notes

- Use fictional data only.
- Do not commit `.env` or secrets.
- The backend is the security boundary.
- Day 1 is backend foundation only: no frontend, risk domain, AI, audit, RAG, CI, or Azure work yet.
