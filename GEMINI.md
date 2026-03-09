# Project Modernization Status: ServerManager (sm)

This document provides context for AI agents working on the modernization of this Django application.

## Current Environment

- **Core:** Python 3.14, Django 6.0.3
- **Frontend:** Bootstrap 4.6.2, Bootswatch Cosmo, Font Awesome 4.7.0, jQuery 3.5.1
- **Auth:** django-allauth (replaced legacy django-user-accounts/urlauth)
- **Serialization:** django-natural-keys (patched for Django 6.0 compatibility)
- **Database:** SQLite (local development/testing)

## Major Achievements

1.  **Framework Upgrade:** Successfully migrated from a Django 1.11/3.1 codebase to Django 6.0.3.
2.  **Authentication:** Fully integrated `django-allauth`. Login, signup, and password reset flows are verified and functional. Social auth links are currently commented out in `_account_bar.html` pending `SocialApp` configuration in the DB.
3.  **UI/UX Overhaul:**
    - Converted all legacy `panel` structures to modern Bootstrap `card` components.
    - Modernized `detail`, `edit`, and `delete` templates with standardized card wrappers and headers.
    - Refactored the navigation bar into logical groups: **Infrastructure**, **Configuration**, and **Clusters**.
    - Standardized pagination via a global `pagination/pagination.html` include.
4.  **Backend Stability:**
    - **View Standardization:** All `CreateView`, `UpdateView`, and `DeleteView` implementations now follow modern Django standards. Specifically, `DeleteView` uses `form_valid` for deletion to ensure success messages are correctly queued.
    - **Message System:** Configured to use `FallbackStorage` to ensure success/error messages persist across redirects during testing and regular use.
    - **Natural Keys:** Applied critical patches to `django.core.serializers` and `natural_keys` in the virtual environment to handle edge cases during fixture loading (e.g., `RelatedObjectDoesNotExist`).
5.  **Test Suite:** All **186 tests** are passing. Test logic has been modernized to use `follow=True` for POST requests and direct message verification in response content.

## Architectural Patterns to Maintain

- **Grouped List Views:** `Operatingsystem` and `Servermodel` list views are grouped by `Vendor`. Their `get_queryset` returns a `Vendor` queryset, and the template iterates over the related set (e.g., `vendor.operatingsystem_set.all`).
- **Success Messages:** Views manually queue messages in `form_valid` using `self.object.__dict__` or similar mappings before redirecting.
- **Pathlib:** All settings and file paths should use `pathlib.Path`.

## Immediate Next Steps

1.  **Linting (High Priority):** Resolve Flake8 errors in `sm/operatingsystem/views.py` and `sm/operatingsystem/test_views.py`. These include unused imports and long lines.
2.  **Cookie Filtering Refinement:** Verify and polish the "Show empty" and "Show disposed" JS/cookie logic in list views to ensure it integrates perfectly with the new card-based layout.
3.  **Social Auth Setup:** Create a `SocialApp` in the admin for Facebook/Google and uncomment the login links in `_account_bar.html`.
4.  **Mobile UI Polish:** Perform a pass on the new grouped navigation to ensure it collapses and behaves correctly on small screens.
5.  **Clean up `venv` Patches:** Move the environment-level patches (`django/core/serializers/base.py` and `natural_keys/models.py`) into the project as proper monkey-patches or overrides if possible, to avoid dependency on a specific modified virtual environment.

## Known Quirks

- The `DeleteView` must use `form_valid` (Django 4.0+ style) to ensure the `object` is still available for the success message template string before it is deleted from the DB.
- Some templates use `{% load bootstrap4 %}` and `{% load i18n %}` which were added systematically; ensure these remain to avoid `TemplateSyntaxError`.
