FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    poppler-utils \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

ENV FLASK_APP=app
ENV FLASK_ENV=production

EXPOSE 5000

# Set proper permissions
RUN chown -R nobody:nogroup /app/uploads
RUN chmod -R 750 /app/uploads

# Add .env support
COPY .env .env