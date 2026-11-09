FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /repo/apps/api

COPY pyproject.toml .
RUN python -c "import tomllib, subprocess, sys; d = tomllib.load(open('pyproject.toml', 'rb')); subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', *d['project']['dependencies'], *d['project']['optional-dependencies']['dev']])"

COPY . .

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
