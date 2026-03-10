# Project Modernization Status: ServerManager (sm)

This document provides context for AI agents working on the modernization of this Django application.

## Current Environment

- **Core:** Python 3.14, Django 6.0.3
- **Frontend:** Bootstrap 4.6.2, Bootswatch Cosmo, Font Awesome 4.7.0, jQuery 3.5.1
- **Auth:** django-allauth (replaced legacy django-user-accounts/urlauth)
- **Serialization:** Native Django Natural Keys (migrated from django-natural-keys)
- **Configuration:** python-decouple with `.env` support and dj-database-url
- **CI/CD:** GitHub Actions (replaced GitLab CI)
- **Database:** SQLite (local development), PostgreSQL (GitHub Actions CI)

## Major Achievements

1.  **Framework Upgrade:** Successfully migrated from a Django 1.11/3.1 codebase to Django 6.0.3.
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
6.  **Test Suite:** All **186 tests** are passing. Test logic has been modernized to use `follow=True` for POST requests and direct message verification.

## Architectural Patterns to Maintain

- **Grouped List Views:** `Operatingsystem` and `Servermodel` list views are grouped by `Vendor`. Their `get_queryset` returns a `Vendor` queryset, and the template iterates over the related set.
- **Success Messages:** Views manually queue messages in `form_valid` using `self.object.__dict__` or similar mappings before redirecting.
- **Pill Buttons:** Always use `.btn` with the modernized pill styling for consistency.
- **Responsive Tables:** Ensure new tables use the standard `.table` class to inherit the mobile-stack behavior.

## Immediate Next Steps

1.  **Production Social Auth:** Configure real `SocialApp` credentials in the production database.
2.  **API Audit:** Review `djangorestframework` serializers and views to ensure they align with the new natural key logic and metadata structure.
3.  **Search Refinement:** Implement or polish global search functionality now that the UI is standardized.

## Known Quirks

- The `DeleteView` must use `form_valid` (Django 4.0+ style) to ensure the `object` is still available for the success message template string before it is deleted.
- Local development uses the `console` email backend via `.env` to prevent mail delivery errors.
