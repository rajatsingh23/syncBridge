FROM python:3.13-slim

# Prevent Python from creating .pyc files
# and enable immediate log output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django backend
COPY backend /app

# Copy and configure the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]