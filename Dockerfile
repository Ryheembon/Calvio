FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

ENV PORT=8000

CMD ["sh", "-c", "echo \"Calvio listening on 0.0.0.0:$PORT\" && uvicorn app.main:app --host 0.0.0.0 --port \"$PORT\""]
