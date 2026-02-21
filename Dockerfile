FROM python:3.10-slim

WORKDIR /app

# Copy and install dependencies first
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Expose the port
EXPOSE 10000

# Start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]