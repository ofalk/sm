# ServerManager (sm)

![CI](https://github.com/ofalk/sm/actions/workflows/ci.yml/badge.svg?branch=main)

A modern Django-based server management application for tracking infrastructure, configurations, and clusters.

Multi-tenancy is supported: servers, clusters, and reference data are scoped to user groups, and quotas/permissions are enforced per group on both the web UI and the API.

## Features

- **Infrastructure Tracking:** Manage vendors, locations, operating systems, and server models.
- **Cluster Management:** Organize servers into clusters with associated software and packages.
- **Multi-Tenancy:** Group-scoped data with per-group quotas and permissions.
- **Modern UI:** Clean, responsive interface built with Bootstrap 5 and Bootswatch Cosmo.
- **Secure Auth:** Integrated with `django-allauth` for robust account management.
- **API Support:** Includes Django Rest Framework for programmatic access.

## Documentation & Reports

- [Coverage Report (GitHub Pages)](https://ofalk.github.io/sm/coverage/)
- [Code Documentation (Pycco)](https://ofalk.github.io/sm/pycco/)

## Quick Start with Docker

The fastest way to test the application is using Docker. This setup uses a local SQLite database.

1. **Build and run the container.** A `SECRET_KEY` is required — the image no
   longer ships an insecure default. For local HTTP, also disable the HTTPS
   redirect (keep it enabled behind a TLS-terminating proxy):

   ```bash
   docker build -t sm .
   docker run -p 8000:8000 \
     -e SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')" \
     -e SECURE_SSL_REDIRECT=False \
     sm
   ```

2. **Access the application:**
   Open [http://localhost:8000](http://localhost:8000) in your browser.
   The admin account is created by the `ensure_admin` entrypoint command; set
   `ADMIN_USERNAME` / `ADMIN_PASSWORD` (see `.env.example`) when running it.

## Local Development

### Prerequisites

- Python 3.13+
- SQLite (default) or PostgreSQL

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ofalk/sm.git
   cd sm
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration:**
   Create a `.env` file in the root directory (see `sm/sm/settings.py` for available options).

   ```env
   SECRET_KEY=your-secret-key
   DEBUG=True
   ```

5. **Run Migrations:**

   ```bash
   cd sm
   python manage.py migrate
   ```

6. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```

### Running Tests

To run the test suite with the default SQLite database:

```bash
python manage.py test
```

To run tests with a specific database (e.g., PostgreSQL):

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/dbname python manage.py test
```

The easiest way to run the suite against PostgreSQL — mirroring CI — is the
bundled helper, which manages a rootless **podman** container for you:

```bash
./pg-test.sh                        # full test discovery (unit + API)
./pg-test.sh --tag=browser          # Playwright browser tests only
./pg-test.sh servermodel clustersoftware   # specific modules
./pg-test.sh --down                 # stop and remove the container
```

## CI/CD

This project uses **GitHub Actions** for continuous integration. The pipeline:

1. Runs a PostgreSQL sidecar container.
2. Executes the full test suite via auto-discovery (`--exclude-tag=browser`), coverage-gated at 85%.
3. Runs the Playwright browser tests (Chromium + Firefox) against PostgreSQL.
4. Generates Pycco documentation.
5. Deploys reports to GitHub Pages on pushes to the `main` branch.
