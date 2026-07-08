FROM python:3.11-slim

# The magic line that fixes the exit code 1
RUN apt-get update && apt-get install -y gcc python3-dev

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# (Keep whatever your original CMD was at the bottom)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]