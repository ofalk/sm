# ServerManager (sm)

![CI](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg?branch=main)

A modern Django-based server management application for tracking infrastructure, configurations, and clusters.

> **Note:** This application is currently **single-tenant**. Multi-tenancy support is on the roadmap.

## Features

- **Infrastructure Tracking:** Manage vendors, locations, operating systems, and server models.
- **Cluster Management:** Organize servers into clusters with associated software and packages.
- **Modern UI:** Clean, responsive interface built with Bootstrap 4.6 and Bootswatch Cosmo.
- **Secure Auth:** Integrated with `django-allauth` for robust account management.
- **API Support:** Includes Django Rest Framework for programmatic access.

## Documentation & Reports

- [Coverage Report (GitHub Pages)](https://<owner>.github.io/<repo>/coverage/)
- [Code Documentation (Pycco)](https://<owner>.github.io/<repo>/pycco/)

## Quick Start with Docker

The fastest way to test the application is using Docker. This setup uses a local SQLite database and pre-loads reasonable defaults.

1. **Build and run the container:**

   ```bash
   docker build -t sm .
   docker run -p 8000:8000 sm
   ```

2. **Access the application:**
   Open [http://localhost:8000](http://localhost:8000) in your browser.
   The container will display a **randomly generated password** for the `admin` user upon startup.

## Local Development

### Prerequisites

- Python 3.14+
- SQLite (default) or PostgreSQL

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/<owner>/<repo>.git
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

## CI/CD

This project uses **GitHub Actions** for continuous integration. The pipeline:

1. Runs a PostgreSQL sidecar container.
2. Executes the full test suite.
3. Checks for minimum 70% code coverage.
4. Generates Pycco documentation.
5. Deploys reports to GitHub Pages on pushes to the `main` branch.
