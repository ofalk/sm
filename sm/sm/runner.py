from django.test.runner import DiscoverRunner


class SmTestRunner(DiscoverRunner):
    """
    Test runner that clears stray PostgreSQL sessions before the test database
    is dropped. Live-server browser tests can leave per-thread sessions behind
    (e.g. when a request aborts mid-view and its handler thread exits without
    closing its connection), which otherwise makes ``DROP DATABASE`` fail with
    ``psycopg.errors.ObjectInUse``.
    """

    def teardown_databases(self, old_config, verbosity=1, keepdb=False):
        from django.db import connections

        for alias in connections:
            connection = connections[alias]
            # NOTE: the vendor string is "postgresql" (not "postgres").
            if connection.vendor != "postgresql":
                continue
            db_name = connection.settings_dict["NAME"]
            # Connect to the maintenance database (not the test DB).
            with connection._nodb_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pid, state, left(coalesce(query, ''), 80)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                    """,
                    [db_name],
                )
                stragglers = cursor.fetchall()
            if stragglers and verbosity >= 2:
                for pid_, state, query in stragglers:
                    print(
                        f"[SmTestRunner] terminating stray session "
                        f"{pid_} ({state}): {query}"
                    )
            with connection._nodb_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                    """,
                    [db_name],
                )
        return super().teardown_databases(
            old_config, verbosity=verbosity, keepdb=keepdb
        )
