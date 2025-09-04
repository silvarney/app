# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        nodejs \
        npm \
        git \
        gettext \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies for Tailwind CSS
COPY package*.json /app/
RUN npm install

# Copy project
COPY . /app/

# Dar permissões de execução para binários Node.js
RUN chmod +x node_modules/.bin/* || true

# Build Tailwind CSS com fallback
RUN npm run build-css-prod || npx --yes tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "saas_project.wsgi:application"]