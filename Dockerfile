FROM python:3.11-slim

WORKDIR /app/backend

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend

ENV DATABASE_TYPE=sqlite
ENV SQLITE_PATH=/data/task_reminder.db
ENV SCHEDULER_INTERVAL_SECONDS=30

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
