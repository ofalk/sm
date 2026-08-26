# Project Modernization Status: ServerManager (sm)

This document provides context for AI agents working on the modernization of this Django application.

## Current Environment

- **Core:** Python 3.14, Django 6.1 (latest stable; 6.0 reached end of mainstream support Aug 2026)
- **Frontend:** Bootstrap 5.3.3, Bootswatch Cosmo 5, Font Awesome 6.7.2, jQuery 3.7.1, Chart.js 4.4.7 (Popper 2 is bundled in `bootstrap.bundle.min.js`)
- **Auth:** django-allauth (replaced legacy django-user-accounts/urlauth)
- **Serialization:** Native Django Natural Keys (migrated from django-natural-keys)
- **Configuration:** python-decouple with `.env` support and dj-database-url
- **CI/CD:** GitHub Actions (replaced GitLab CI)
- **Database:** SQLite (local development), PostgreSQL (GitHub Actions CI). Locally, `./pg-test.sh` runs the suite against PostgreSQL in a rootless podman container, mirroring CI.

## Major Achievements

1.  **Framework Upgrade:** Successfully migrated from a Django 1.11/3.1 codebase to Django 6.1.
2.  **CI/CD Modernization:**
    - Migrated from GitLab CI to **GitHub Actions**, targeting the `main` branch.
    - Implemented a **PostgreSQL sidecar container** in the CI pipeline for more realistic test environments.
    - Automated the generation and publishing of **Pycco documentation** and **Coverage HTML reports** to GitHub Pages.
    - Integrated `dj-database-url` for flexible database configuration via environment variables.
3.  **Authentication & Account Modernization:**
    - Fully integrated `django-allauth`. Login, signup, password reset, and email management flows are verified and functional.
    - Modernized all account templates (Login, Signup, Social Connections, Email Management) with a professional two-column sidebar layout and card-based design.
    - Social Auth links are styled and ready (Facebook/Google), pending production `SocialApp` keys.
4.  **UI/UX Overhaul:**
    - **Consistent Layout:** Introduced `.wide-container` for balanced, responsive horizontal spacing across the entire application.
    - **Standardized Buttons:** All buttons now follow a modern pill-style design (`border-radius: 2rem`) with consistent sizing (`btn-sm`).
    - **Modern Tables:** Tables have been overhauled with a "clean card-list" look, increased padding, and hovering effects.
    - **Responsive Stack:** Implemented a CSS/JS solution that automatically transforms dense tables into mobile-friendly card stacks on small screens.
    - **Navigation:** Refactored the navbar into logical groups: **Infrastructure**, **Configuration**, and **Clusters**.
5.  **Backend Stability & Modernization:**
    - **Metadata Upgrade:** Migrated all models from legacy `unique_together` to modern Django `UniqueConstraint`.
    - **Clean Models:** Removed redundant `app_label` and `managed` attributes from all model `Meta` classes.
    - **Native Natural Keys:** Completely removed the `django-natural-keys` dependency in favor of native Django `natural_key` and `get_by_natural_key` implementations.
    - **Robust Serialization:** Formalized critical serialization patches in `sm/sm/patches.py` to handle fixture loading edge cases.
6.  **Test Suite:** **469 unit/API tests** run in CI via auto-discovery (`manage.py test --exclude-tag=browser`, coverage-gated ≥70% through `.coveragerc`), plus **5 Playwright browser tests** (`--tag=browser`, Chromium + Firefox: JS/resource integrity scans, CRUD workflow, multi-tenancy browser isolation, and a full integration CRUD/safe-delete suite). A custom `SmTestRunner` (`sm/sm/runner.py`) terminates stray PostgreSQL sessions before dropping the test database, and settings force `CONN_MAX_AGE=0` during tests. The suite includes dedicated multi-tenancy isolation tests (web, API, history, FK scoping, global-fixture immutability) in `sm/sm/test_multitenancy_isolation.py`. Test logic uses `follow=True` for POST requests and direct message verification.
7.  **REST API:** The full data model is exposed via Django REST Framework ViewSets (`/api/`), with OpenAPI docs at `/api/schema/`. All ViewSets apply group-based multi-tenancy filtering, enforce model permissions (including `view_` for reads), and support **pagination, search/ordering filters, and throttling**.
8.  **API Keys:** Users can generate `client_id`/secret credential pairs from *API Keys* in their account menu (`/account/api-keys/`). Keys authenticate via `Authorization: ApiKey <client_id>:<secret>` and grant exactly the access of the owning user (group permissions included). Secrets are stored hashed and shown only once.
9.  **Bootstrap 5 Migration:** Migrated from EOL Bootstrap 4.6.2/`django-bootstrap4` to **Bootstrap 5.3.3** + **`django-bootstrap5`**. This included updating the CDN assets (Bootswatch Cosmo 5, bundled Popper), renaming template tags (`{% load bootstrap4 %}` → `{% load django_bootstrap5 %}`), replacing removed tags (`{% buttons %}`), and migrating markup (`data-*` → `data-bs-*`, `mr-*`/`ml-*`/`pr-*`/`pl-*` → `me-*`/`ms-*`/`pe-*`/`ps-*`, `form-group` → `mb-3`, custom form controls → `form-check`/`form-switch`, input-group wrappers, `badge-*` → `text-bg-*`, `btn-block` → `d-block w-100`, `.close` → `.btn-close`, `jumbotron`). The command palette modal now uses the Bootstrap 5 JS API instead of the removed jQuery plugin.
10.  **Feature Expansion (2026-08):** Bulk operations and CSV export across all models; API key lifecycle (expiry, rotation, cleanup); server lifecycle tracking with decommission date; profile page, onboarding flow, audit log, and patch schedule views; taggit tags on several models; broader global search with group filter; status-change notifications; a German translation catalog; and the monitoring flag renamed to "Monitoring" with a legacy API alias.

## Architectural Patterns to Maintain

- **Multi-Tenancy:** All tenant models carry an immutable `group` FK. Views/APIs filter via `sm.mixins.MultiTenantMixin` / `APIMultiTenantMixin`. Global (group-less) seed fixtures are read-only for tenant users on web, API, and bulk paths. Grouped list views that return `Vendor` rows set `model = VendorModel` plus a `permission_model` hook so permission checks stay anchored to their own app.
- **Uniqueness:** Tenant models use group-inclusive `UniqueConstraint`s. Because PostgreSQL treats NULLs as distinct, models with global reference data additionally carry **partial unique constraints** on `(fields… WHERE group IS NULL)` so superusers cannot create duplicate globals (which would break natural-key lookups). Follow this pattern for new tenant models with shared reference data — see `servermodel`/`clustersoftware` for examples.

- **Success Messages:** Views manually queue messages in `form_valid` using `self.object.__dict__` or similar mappings before redirecting.
- **Pill Buttons:** Always use `.btn` with the modernized pill styling for consistency.
- **Responsive Tables:** Ensure new tables use the standard `.table` class to inherit the mobile-stack behavior.

## Immediate Next Steps

1.  **Production Social Auth:** Configure real `SocialApp` credentials in the production database.
2.  **Multi-Tenancy:** Data isolation across all apps is complete; the isolation suites run in CI. The canonical reference is `MULTI_TENANCY_DEVELOPER_GUIDE.md`; the redundant `MULTI_TENANCY.md` and stale `MULTITENANCY_STATUS.md` were removed during documentation consolidation.
3.  **Security Hardening:** `SECRET_KEY` is required when `DEBUG=False` (with `SECURE_*` settings enabled), `.env` is git-ignored (see `.env.example`), and the entrypoint writes the generated admin password to `/app/.admin_password` instead of stdout.

## Known Quirks

- The `DeleteView` must use `form_valid` (Django 4.0+ style) to ensure the `object` is still available for the success message template string before it is deleted.
- Local development uses the `console` email backend via `.env` to prevent mail delivery errors.
- The `server.Model` model declares `default=timezone.now` on its `DateField`s (which yields datetimes); the REST API serializers tolerate this via a custom `CoercingDateField`.
