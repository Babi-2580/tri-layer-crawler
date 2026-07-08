# 1. Use the official Playwright image (Chromium and dependencies are already inside!)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# 2. Install your standard Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy your worker code
COPY . .

# 4. Run the worker (Adjust main.py if your script is named differently)
CMD ["python", "main.py"]