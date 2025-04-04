# Use lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    poppler-utils \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# 2. Update pip and setuptools first
RUN pip install --upgrade pip setuptools wheel

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Set Flask environment variables (use Render Dashboard for .env)
ENV FLASK_APP=app
ENV FLASK_ENV=production

# Expose application port
EXPOSE 5000

# Set proper permissions for uploads
RUN chown -R nobody:nogroup /app/uploads
RUN chmod -R 750 /app/uploads

# REMOVE `.env` COPY LINE (Render provides env vars)
# COPY .env .env  ❌ Removed

# Start the Flask application
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
# Final CMD should be:
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--preload", "run:app"]


# CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "2", "--preload", ":create_app()"]