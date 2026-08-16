from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def set_sqlite_pragmas(sender, connection, **kwargs):
    """
    Harden SQLite connections against concurrent access (live server threads
    + test runner). WAL mode allows concurrent readers/writers, and a busy
    timeout makes writers wait instead of failing with "database is locked".
    """
    if connection.vendor != "sqlite":
        return
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=30000;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
