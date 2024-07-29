# Use the official Python image as a base image
FROM python:3.10-slim

# Set environment variables to prevent Python from writing .pyc files and buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for mysqlclient
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to /app in the container
COPY . /app/

# # Collect static files (assuming you have set up Django to collect static files)
# RUN python manage.py collectstatic --noinput

# Apply database migrations
RUN python manage.py makemigrations
RUN python manage.py migrate

# Expose port 8000 for the Django application
EXPOSE 8000

# Start the Django application using Gunicorn
CMD ["gunicorn", "GEN_AI_BACKEND.wsgi:application", "--bind", "0.0.0.0:8000"]
