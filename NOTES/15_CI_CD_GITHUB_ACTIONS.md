# 🚀 15. CI/CD with GitHub Actions & Docker: Testing, Environments, & Deployment

> **Goal:** Master Continuous Integration and Continuous Deployment (CI/CD) from scratch. Learn how GitHub Actions automates testing with a live MySQL service container, builds optimized Docker images using BuildKit layer caching, pushes to Docker Hub with dual tags, and how production deployment works when you're ready.

---

## 📌 1. What is CI/CD & Why Is It Essential?

### The "Old School" Developer Nightmare
Imagine working on a team or pushing updates to a live API without CI/CD:
1. You change a router function on your Mac and forget to run your tests.
2. You commit and push straight to the `main` branch.
3. Your code is pulled onto the server.
4. **Crash!** A library was missing from `requirements.txt`, or an unhandled query breaks the database.
5. Users see `500 Internal Server Error`, and you spend hours panicking to find out which commit broke it.

### The Modern Way: The CI/CD Pipeline
A **CI/CD Pipeline** is an automated factory that checks, tests, and packages your software every time you make a commit:

```
                                  THE CI/CD LIFECYCLE
                                  
   Developer writes code
            │
            ▼
    git push origin main
            │
            ▼
┌───────────────────────────────────────────────────────────────┐
│ 1. CONTINUOUS INTEGRATION (CI)                                │
│    • GitHub spins up an isolated Ubuntu 24.04 runner          │
│    • GitHub starts a MySQL 8 service container on port 3306   │
│    • Sets up Python 3.13 & installs dependencies from cache   │
│    • Auto-provisions main DB and test DB                      │
│    • Runs 35+ Pytest tests                                    │
│    • ❌ Any test fails? Build halts, email sent, merge blocked│
│    • ✅ All tests pass? Proceed to packaging                  │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│ 2. DOCKER PACKAGING & HUB PUBLISHING                          │
│    • Uses BuildKit (Docker Buildx)                            │
│    • Reads .dockerignore to skip virtualenvs & secrets        │
│    • Logs into Docker Hub using encrypted secrets             │
│    • Pulls cached layers from GitHub Actions Cache (GHA)      │
│    • Tags image with :latest AND git commit SHA               │
│    • Pushes image to your Docker Hub repository               │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│ 3. CONTINUOUS DEPLOYMENT (CD) [When Ready for Production]     │
│    • Triggers only on approved merges to main                 │
│    • Connects to production server via SSH                    │
│    • Pulls new image from Docker Hub                          │
│    • Restarts container with zero manual SSH commands         │
└───────────────────────────────────────────────────────────────┘
```

| Term | Full Name | Purpose | What Happens If It Fails? |
| :--- | :--- | :--- | :--- |
| **CI** | Continuous Integration | Merge and test code automatically. | Build fails, code is rejected before reaching production. |
| **CD** | Continuous Delivery / Deployment | Package and release working code to users. | Rollback to the previous stable Docker image tag. |

---

## 🐙 2. Anatomy of GitHub Actions

GitHub Actions looks for YAML files inside `.github/workflows/`.
> ⚠️ **Common Beginner Trap:** The folder **must** be named `.github/workflows/` (plural). If you name it `.github/workflow/`, GitHub completely ignores it!

### The Building Blocks:

```yaml
name: Test and Build Docker Image       # 1. Workflow Name

on:                                     # 2. Trigger Events
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:                                   # 3. Jobs (Runners)
  build:
    runs-on: ubuntu-latest              # Virtual Machine OS
    environment:                        # 4. GitHub Environment Binding
      name: testing
    services:                           # 5. Auxiliary Containers
      mysql: ...
    steps:                              # 6. Step-by-step instructions
      - uses: actions/checkout@v4
      - run: pytest -v
```

1. **Workflow:** The automated process from start to finish.
2. **Events (`on`):** Triggers like `push` or `pull_request`.
3. **Jobs:** Units of work. By default, separate jobs run in parallel unless linked with `needs: [job_name]`.
4. **Runners:** Fresh virtual machines provided by GitHub (e.g., `ubuntu-latest`).
5. **Steps:** Individual actions (`uses: ...`) or terminal commands (`run: ...`).
6. **Services:** Docker containers attached to the runner network (e.g., MySQL, Redis).

---

## 🔐 3. GitHub Environments vs Repository Secrets

GitHub provides two levels of secret storage under **Repository Settings → Secrets and variables**:

```
GitHub Repository
   ├── Repository Secrets (Accessible by ANY job in ANY workflow)
   │
   └── Environments (e.g., "testing", "production")
         └── Environment Secrets (Accessible ONLY if the job specifies environment: <name>)
```

### Why Did We Configure `environment: name: testing`?
In our project, all database and Docker credentials are saved inside the **`testing`** environment.
If a job doesn't have `environment: name: testing`, all `${{ secrets.DATABASE_* }}` and `${{ secrets.DOCKER_HUB_* }}` will evaluate to **empty strings** (`""`), causing database connection errors or Docker login failures!

### Exact Secrets Used in Our `testing` Environment:

| Secret Key | Example Value | Why We Need It |
| :--- | :--- | :--- |
| `DATABASE_HOSTNAME` | `127.0.0.1` | Host where the runner reaches the MySQL service. |
| `DATABASE_PORT` | `3306` | Default MySQL port. |
| `DATABASE_NAME` | `FastAPI` | Main database name. |
| `DATABASE_USERNAME` | `root` | MySQL user. |
| `DATABASE_PASSWORD` | `vanshtank` | MySQL password for service and test connection. |
| `SECRET_KEY` | `your_jwt_secret_key` | Secret used to sign and verify JWT authentication tokens. |
| `ALGORITHM` | `HS256` | Cryptographic algorithm for JWTs. |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| `30` | Token expiration time. |
| `DOCKER_HUB_USERNAME` | `your_username` | Docker Hub username for login and image naming. |
| `DOCKER_HUB_TOKEN` | `dckr_pat_xxxx` | Docker Hub Personal Access Token (PAT). |

---

## 🗄️ 4. The MySQL 8 Service Container Deep Dive

When your tests run on GitHub Actions, where does MySQL come from?
GitHub allows you to run **Service Containers** alongside the runner:

```yaml
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
        ports:
          - 3306:3306
        options: >-
          --health-cmd "mysqladmin ping -h 127.0.0.1 -u root -proot"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
```

### Critical Details You Must Know:
1. **The `secrets` Context is NOT Allowed in `services:`**
   - In GitHub Actions, the `services:` block is parsed **before** the job's environment secrets are evaluated. If you write `${{ secrets.DATABASE_PASSWORD }}` inside `services:`, GitHub Actions throws:
     `Unrecognized named-value: 'secrets'`.
   - **The Solution:** Start the ephemeral test service with a default static password (`root`), and in the very first step (`Ensure test database and users exist`), update the credentials and databases using your environment secrets!
2. **`MYSQL_ROOT_PASSWORD` is mandatory:** In MySQL 8, the official container will crash immediately if `MYSQL_ROOT_PASSWORD` is omitted.
3. **`--health-cmd`:** Steps will not run until the MySQL service responds `mysqld is alive`. The runner tests health every 10 seconds up to 5 times.
3. **The `localhost` vs `127.0.0.1` Linux Trap:**
   - On Linux (which `ubuntu-latest` runs), if an application connects to `localhost`, the MySQL client tries to open a Unix socket file at `/tmp/mysql.sock` (which fails because the container is running over TCP).
   - Connecting to `127.0.0.1` forces TCP/IP over port `3306`.
   - In our workflow, we protect against this with:
     ```yaml
     DATABASE_HOSTNAME: ${{ secrets.DATABASE_HOSTNAME == 'localhost' && '127.0.0.1' || secrets.DATABASE_HOSTNAME }}
     ```

---

## 🧪 5. Auto-Provisioning Both Databases (`app` and `_test`)

In our project architecture:
- `app/database.py` connects to `DATABASE_NAME` (e.g., `FastAPI`).
- `tests/conftest.py` connects to `f"{DATABASE_NAME}_test"` (e.g., `FastAPI_test`).

When the MySQL container boots, it only creates `DATABASE_NAME`. If `pytest` runs immediately, `conftest.py` crashes with:
```
(pymysql.err.OperationalError) (1049, "Unknown database 'FastAPI_test'")
```

### The Solution: Pre-Test Provisioning Step
Before running `pytest`, we run a short inline Python script:
```python
import pymysql
host = '127.0.0.1' if '${{ secrets.DATABASE_HOSTNAME }}' in ['localhost', ''] else '${{ secrets.DATABASE_HOSTNAME }}'
conn = pymysql.connect(
    host=host,
    port=int('${{ secrets.DATABASE_PORT }}'),
    user='root',
    password='${{ secrets.DATABASE_PASSWORD }}'
)
cur = conn.cursor()
cur.execute('CREATE DATABASE IF NOT EXISTS `${{ secrets.DATABASE_NAME }}`;')
cur.execute('CREATE DATABASE IF NOT EXISTS `${{ secrets.DATABASE_NAME }}_test`;')
if '${{ secrets.DATABASE_USERNAME }}' != 'root':
    cur.execute("CREATE USER IF NOT EXISTS '${{ secrets.DATABASE_USERNAME }}'@'%' IDENTIFIED BY '${{ secrets.DATABASE_PASSWORD }}';")
    cur.execute("GRANT ALL PRIVILEGES ON *.* TO '${{ secrets.DATABASE_USERNAME }}'@'%';")
    cur.execute("FLUSH PRIVILEGES;")
conn.close()
```
This guarantees:
- Both databases exist.
- User permissions are granted even if `DATABASE_USERNAME` is not `root`.
- Tests run cleanly with 0 configuration errors!

---

## 🐳 6. Docker Build & Push Pipeline

Once tests pass, the same workflow builds and pushes your Docker container:

```yaml
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
          tags: |
            ${{ secrets.DOCKER_HUB_USERNAME }}/fastapi-posts:latest
            ${{ secrets.DOCKER_HUB_USERNAME }}/fastapi-posts:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Key Concepts Explained:

#### 1. Why Docker Buildx?
Standard `docker build` is legacy. **Docker Buildx** uses the **BuildKit** engine, which provides:
- Parallel stage execution.
- Advanced layer caching.
- Multi-platform building (e.g., AMD64 for cloud servers, ARM64 for Apple Silicon).

#### 2. GitHub Actions Layer Caching (`type=gha`)
Normally, building a Docker image on a remote runner takes 2–4 minutes because every pip package has to be downloaded from scratch.
- `cache-to: type=gha,mode=max`: Saves intermediate image layers into GitHub's cloud cache.
- `cache-from: type=gha`: On the next commit, Docker reuses unchanged layers. Builds finish in **under 15 seconds**!

#### 3. Dual Tagging Strategy
Notice we push two tags:
- `:latest`: Always points to the most recent working build.
- `:${{ github.sha }}`: The unique 40-character Git commit hash (e.g. `fastapi-posts:4b37208...`).
  - **Why is commit SHA tagging critical?**
    If version `:latest` has an unexpected bug in production, you don't need to rebuild or recompile code. You can simply roll back your container to the previous commit hash in **1 second**!

#### 4. Conditional Pushing (`push: ...`)
- If someone opens a **Pull Request**, Docker builds the image to verify there are no compilation or syntax errors, but sets `push: false` (does not pollute Docker Hub).
- When merged into **`main`**, `push: true` publishes the image to Docker Hub.

---

## 📄 7. The `.dockerignore` Shield

Before Docker sends files to the daemon, it reads [`.dockerignore`](../.dockerignore):

```dockerignore
__pycache__/
*.pyc
venv/
.venv/
.git/
.github/
.pytest_cache/
tests/
NOTES/
SQL_learn/
.env
app/.env
*.db
mydb.db
```

### Why each entry matters:
- **`.env` and `app/.env`:** NEVER put secret `.env` files into Docker images. Docker images pushed to Docker Hub can be inspected by anyone with access.
- **`venv/`:** Virtualenvs built on macOS will NOT run inside a Debian Linux Docker container (`python:3.13-slim`).
- **`tests/` & `NOTES/`:** Your production Docker image should contain only the code needed to serve API requests, keeping image size minimal.

---

## 🚢 8. How Production Deployment (CD) Works (When You're Ready)

Right now, your workflow focuses on **testing and Docker publishing** in your `testing` environment.
When you are ready to connect a live production server (e.g., AWS EC2, DigitalOcean Droplet, Linode, or a Raspberry Pi), here is how automated CD works.

### Approach 1: Deploying via SSH (`appleboy/ssh-action`)
In this approach, GitHub Actions logs into your Linux server over SSH, pulls the Docker image, and restarts the container:

```yaml
  deploy:
    name: Deploy to Production
    needs: [build]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: production

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.2.0
        with:
          host: ${{ secrets.PROD_HOST }}          # Server IP (e.g., 143.198.xxx.xxx)
          username: ${{ secrets.PROD_USERNAME }}  # Linux user (e.g., ubuntu)
          key: ${{ secrets.PROD_SSH_KEY }}        # Private SSH key
          script: |
            echo "1. Pulling latest image..."
            docker pull ${{ secrets.DOCKER_HUB_USERNAME }}/fastapi-posts:latest
            
            echo "2. Stopping existing container..."
            docker stop fastapi-app || true
            docker rm fastapi-app || true
            
            echo "3. Running updated container..."
            docker run -d \
              --name fastapi-app \
              --restart always \
              -p 8000:8000 \
              --env-file /home/ubuntu/.env \
              ${{ secrets.DOCKER_HUB_USERNAME }}/fastapi-posts:latest
              
            echo "🚀 Deployment Successful!"
```

### Approach 2: Deploying with Docker Compose on the Server
If your server runs both MySQL and FastAPI using `docker-compose.yml`:
```bash
# Inside the SSH deploy step:
cd /home/ubuntu/FastAPI_Post_Project
docker compose pull api
docker compose up -d --no-deps api
```
- `--no-deps api` tells Compose to recreate only the FastAPI application without restarting or interrupting the MySQL database container!

### Approach 3: Cloud Platform Webhooks (Render / Railway / Fly.io)
If hosting on a platform like Render or Railway:
1. Under your service settings, copy the **Deploy Hook URL**.
2. Add it as a secret: `RENDER_DEPLOY_HOOK`.
3. In GitHub Actions, simply call it with `curl`:
```yaml
      - name: Trigger Cloud Deploy
        run: curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK }}"
```

---

## 🛠️ 9. Complete Current Workflow File (`build-deploy.yml`)

Here is your exact workflow in [`.github/workflows/build-deploy.yml`](../.github/workflows/build-deploy.yml):

```yaml
name: Build and Deploy

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  build:
    name: Test and Build Docker Image
    runs-on: ubuntu-latest
    environment:
      name: testing

    env:
      DATABASE_HOSTNAME: ${{ secrets.DATABASE_HOSTNAME == 'localhost' && '127.0.0.1' || secrets.DATABASE_HOSTNAME }}
      DATABASE_PORT: ${{ secrets.DATABASE_PORT }}
      DATABASE_NAME: ${{ secrets.DATABASE_NAME }}
      DATABASE_USERNAME: ${{ secrets.DATABASE_USERNAME }}
      DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
      SECRET_KEY: ${{ secrets.SECRET_KEY }}
      ALGORITHM: ${{ secrets.ALGORITHM }}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${{ secrets.ACCESS_TOKEN_EXPIRE_MINUTES }}

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
        ports:
          - 3306:3306
        options: >-
          --health-cmd "mysqladmin ping -h 127.0.0.1 -u root -proot"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.13
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"
          cache: "pip"

      - name: Upgrade pip
        run: python -m pip install --upgrade pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Ensure test database and users exist
        run: |
          python -c "
          import pymysql
          conn = pymysql.connect(
              host='127.0.0.1',
              port=3306,
              user='root',
              password='root'
          )
          cur = conn.cursor()
          cur.execute('CREATE DATABASE IF NOT EXISTS \`${{ secrets.DATABASE_NAME }}\`;')
          cur.execute('CREATE DATABASE IF NOT EXISTS \`${{ secrets.DATABASE_NAME }}_test\`;')
          cur.execute(\"ALTER USER 'root'@'%' IDENTIFIED BY '${{ secrets.DATABASE_PASSWORD }}';\")
          cur.execute(\"ALTER USER 'root'@'localhost' IDENTIFIED BY '${{ secrets.DATABASE_PASSWORD }}';\")
          if '${{ secrets.DATABASE_USERNAME }}' != 'root':
              cur.execute(\"CREATE USER IF NOT EXISTS '${{ secrets.DATABASE_USERNAME }}'@'%' IDENTIFIED BY '${{ secrets.DATABASE_PASSWORD }}';\")
              cur.execute(\"GRANT ALL PRIVILEGES ON *.* TO '${{ secrets.DATABASE_USERNAME }}'@'%';\")
          cur.execute(\"FLUSH PRIVILEGES;\")
          conn.close()
          print('Databases and credentials initialized successfully!')
          "

      - name: Run pytest test suite
        run: pytest -v

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
          tags: |
            ${{ secrets.DOCKER_HUB_USERNAME }}/fastapi-posts:latest
            ${{ secrets.DOCKER_HUB_USERNAME }}/fastapi-posts:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## ❓ 10. Frequently Asked Questions & Troubleshooting

### Q1: "Why did my GitHub Actions run say `Docker login failed: Username and password required`?"
- **Cause:** You didn't declare `environment: name: testing` at the job level.
- **Fix:** Ensure the job includes:
  ```yaml
  environment:
    name: testing
  ```

### Q2: "Why does pytest complain that `FastAPI_test` database doesn't exist?"
- **Cause:** MySQL container only creates the database given in `MYSQL_DATABASE`.
- **Fix:** Keep the `Ensure test database and users exist` step before `pytest -v`.

### Q3: "Should I use my Docker Hub account password or an Access Token?"
- **Always use a Personal Access Token (PAT):**
  1. Go to [hub.docker.com](https://hub.docker.com) → **Account Settings** → **Security**.
  2. Click **New Access Token**.
  3. Give it description `GitHub Actions` and **Read & Write** access.
  4. Paste that token into GitHub Secrets as `DOCKER_HUB_TOKEN`.
  5. A PAT can be revoked at any time without compromising your primary Docker Hub account password!

### Q4: "How do I roll back if a release introduces a bug?"
Because your workflow tags every build with `:${{ github.sha }}`, you don't have to rebuild:
```bash
# On your server, pull the exact commit that was working:
docker pull yourusername/fastapi-posts:4b37208471e48cd6773d78044411db28c7925006
docker stop fastapi-app && docker rm fastapi-app
docker run -d --name fastapi-app yourusername/fastapi-posts:4b37208471e48cd6773d78044411db28c7925006
```
Your service is instantly rolled back to the healthy version!
