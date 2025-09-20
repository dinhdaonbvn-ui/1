# Simple image running FastAPI backend and serving /frontend as static
FROM python:3.11-slim

WORKDIR /app
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r backend/requirements.txt

# Use uvicorn to run backend; static frontend will be mounted from /app/frontend
EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000", "--reload"]
