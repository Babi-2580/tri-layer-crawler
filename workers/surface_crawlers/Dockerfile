# Use official Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy your requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your worker code
COPY . .

# Command to run your worker (adjust 'main.py' if your script has a different name)
CMD ["python", "main.py"]