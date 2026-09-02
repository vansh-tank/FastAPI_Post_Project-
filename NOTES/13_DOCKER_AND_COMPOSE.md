# 🐳 13. Docker & Docker Compose

> **Goal:** Understand how to containerize the FastAPI application and MySQL database, run them together using Docker Compose, and ensure database migrations run automatically.

---

## 📌 1. What is Docker & Why Do We Use It?

### The Problem: "It works on my machine!"
When developing locally:
- You have Python 3.13 installed on macOS.
- You have a local MySQL server installed and running.
- When you deploy to a Linux cloud server (AWS, DigitalOcean, etc.), Python versions, system libraries, or MySQL configurations might differ, causing errors.

### The Solution: Containers
**Docker** packages your application, its code, runtime, system tools, and dependencies into an isolated unit called a **Container**.
- If it runs in Docker on your laptop, it will run **identically** on any server in the world.

| Concept | Explanation | Real-world Analogy |
| :--- | :--- | :--- |
| **Dockerfile** | A recipe with step-by-step instructions to build an image. | A blueprint / recipe book |
| **Image** | The compiled, packaged template containing OS + code + libraries. | A frozen pizza |
| **Container** | A running instance of an image. | The cooked pizza being eaten |
| **Docker Compose** | A tool to run and coordinate multiple containers (e.g. FastAPI + MySQL). | The chef managing the entire meal |

---

## 📄 2. The Dockerfile Explained

Here is the [`Dockerfile`](../Dockerfile) used for our FastAPI app:

```dockerfile
# 1. Base Image
FROM python:3.13-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy only requirements first (for Docker caching)
COPY requirements.txt ./

# 4. Install dependencies
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the project source code
COPY . .

# 6. Command to start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 💡 Why Copy `requirements.txt` Before `COPY . .`?
Docker builds images in **layers** and caches them.
- If you edit a Python file (e.g. `main.py`), Docker knows `requirements.txt` didn't change, so it **skips reinstalling all pip packages** and finishes the build in under 1 second!

---

## 🐙 3. Docker Compose Explained (`docker-compose.yml`)

When your app needs both an **API service** and a **MySQL Database**, running them manually in separate Docker commands is tedious. **Docker Compose** orchestrates them together with a single command.

Here is the complete [`docker-compose.yml`](../docker-compose.yml):

```yaml
services:
  mysql:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: vanshtank
      MYSQL_DATABASE: FastAPI
    ports:
      - "2000:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-pvanshtank"]
      interval: 5s
      timeout: 5s
      retries: 10

  api:
    build: .
    ports:
      - "8000:8000"
    command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
    environment:
      - DATABASE_HOSTNAME=mysql
      - DATABASE_PORT=3306
      - DATABASE_NAME=FastAPI
      - DATABASE_USERNAME=root
      - DATABASE_PASSWORD=vanshtank
      - SECRET_KEY=secret
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
    depends_on:
      mysql:
        condition: service_healthy
    volumes:
      - .:/app

volumes:
  mysql_data:
```

---

## 🔍 4. Key Concepts in Docker Compose

### A. Networking & DNS
- Docker Compose automatically creates a private virtual network.
- Containers communicate using their **service name as the hostname**.
- The API container connects to MySQL using `DATABASE_HOSTNAME=mysql` (NOT `localhost`).

### B. Port Mapping (`HOST : CONTAINER`)
- **`8000:8000` (API)**: Maps port `8000` on your Mac to port `8000` inside the container.
- **`2000:3306` (MySQL)**: Maps port `2000` on your Mac to port `3306` in MySQL. You can inspect MySQL from TablePlus/DBeaver on port `2000` on your host.

### C. Persistent Storage (Volumes)
Containers are ephemeral (temporary). If a container is destroyed, its internal files disappear.
- `volumes: - mysql_data:/var/lib/mysql` persists database files on your host storage so you never lose data across restarts.

### D. Healthchecks & Startup Order
MySQL takes 5–10 seconds to initialize tables on first boot.
- `healthcheck` continuously tests if MySQL is ready to accept connections.
- `depends_on: mysql: condition: service_healthy` tells Docker **to hold the API container** until MySQL is 100% healthy.

### E. Automatic Database Migrations (`sh -c`)
```yaml
command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
```
- **`sh -c`**: Runs a shell command string.
- Runs `alembic upgrade head` to automatically create/update database tables.
- If migrations succeed (`&&`), starts `uvicorn` to serve traffic.

---

## ⚡ 5. Essential Docker Commands

| Command | What it does |
| :--- | :--- |
| `docker compose up --build` | Builds images and starts all containers in the foreground with live logs. |
| `docker compose up -d --build` | Starts containers in the background (detached mode). |
| `docker compose logs -f` | Follows and displays real-time logs from all containers. |
| `docker compose logs -f api` | Follows logs from only the `api` container. |
| `docker compose down` | Stops and removes all containers and networks. |
| `docker compose down -v` | Stops containers and **deletes volumes** (resets the database to empty). |
| `docker ps` | Lists all currently running containers. |
| `docker exec -it <container_id> bash` | Opens an interactive terminal shell inside a running container. |

---

## 🛠️ 6. Troubleshooting Common Issues

### Issue 1: `pip install` fails with exit code 1
- **Reason:** macOS-only packages (like `pyobjc`) or incompatible binary wheels in `requirements.txt`.
- **Fix:** Keep `requirements.txt` clean with only platform-independent dependencies.

### Issue 2: `Table 'FastAPI.users' doesn't exist`
- **Reason:** Migrations were not applied to the newly created database container.
- **Fix:** Ensure the `command:` in `docker-compose.yml` runs `alembic upgrade head` before `uvicorn`.

### Issue 3: `Can't connect to MySQL server on 'localhost'`
- **Reason:** Inside a Docker container, `localhost` points to the container itself, not the database container.
- **Fix:** Use `DATABASE_HOSTNAME=mysql`.
