FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything else
COPY . .

# Force the app to bind to 0.0.0.0 (Public) and Port 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]