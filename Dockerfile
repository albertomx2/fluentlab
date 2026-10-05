FROM python:3.13-alpine
WORKDIR /app
RUN apk add --no-cache ca-certificates
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY static ./static
RUN mkdir -p /data
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
