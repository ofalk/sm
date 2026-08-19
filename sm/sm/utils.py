import hashlib
import random
import string


def get_email_hash(email):
    """
    Returns MD5 hash of lowercase email for avatar services.
    """
    if not email:
        return "00000000000000000000000000000000"
    return hashlib.md5(email.lower().encode("utf-8")).hexdigest()


def random_string(len=10):
    return "".join(
        random.SystemRandom().choice(string.ascii_lowercase + string.digits)
        for _ in range(10)
    )


def random_number(start=0, end=10):
    return random.randint(start, end)
