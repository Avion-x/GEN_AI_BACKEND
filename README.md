# TestCase Generation Project

## Prerequisites
Ensure you have the following installed:
- Python
- Django 
- Docker
- Docker Compose

## Installation

### Without Docker
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo.git
   cd your-repo
   ```
2. Create a virtual environment and activate it:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scriptsctivate`
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Apply migrations:
   ```sh
   python manage.py migrate
   ```
5. Run the development server:
   ```sh
   python manage.py runserver
   ```

## Dockerizing the Django Application

### Step 1: Create a `Dockerfile`
Ensure you have a `Dockerfile` in your project root with the following content:

```dockerfile
# Use official Python image as base
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the application files to the container
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### Step 2: Create a `docker-compose.yml`
Create a `docker-compose.yml` file for easy container management:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DEBUG=True
    depends_on:
      - db
  db:
    image: postgres:13
    restart: always
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydatabase
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Step 3: Build and Run the Containers
Run the following command to build and start the containers:

```sh
docker-compose up --build
```

To stop the containers, run:

```sh
docker-compose down
```

## Running Migrations in Docker
After starting the containers, run migrations inside the Django container:

```sh
docker-compose exec web python manage.py migrate
```

## Accessing the Application
Once the containers are running, open [http://localhost:8000](http://localhost:8000) in your browser.

