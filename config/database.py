from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured


def build_database_settings(database_url: str | None, debug: bool, sqlite_path: Path) -> dict:
    if not database_url:
        if not debug:
            raise ImproperlyConfigured("DATABASE_URL must point to PostgreSQL when DJANGO_DEBUG is false.")
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": sqlite_path}

    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname or not parsed.path.strip("/"):
        raise ImproperlyConfigured("DATABASE_URL must be a PostgreSQL URL with a database name and host.")
    if not debug and (not parsed.username or not parsed.password):
        raise ImproperlyConfigured("Production DATABASE_URL must include database credentials.")

    try:
        port = parsed.port
    except ValueError as error:
        raise ImproperlyConfigured("DATABASE_URL contains an invalid port.") from error

    query = parse_qs(parsed.query)
    if any(len(values) != 1 for values in query.values()):
        raise ImproperlyConfigured("DATABASE_URL cannot repeat connection options.")
    sslmode = query.get("sslmode", ["prefer" if debug else "require"])[0]
    if not debug and sslmode not in {"require", "verify-ca", "verify-full"}:
        raise ImproperlyConfigured("Production DATABASE_URL must use TLS (sslmode=require or stronger).")

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname,
        "PORT": str(port or 5432),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {**{name: values[0] for name, values in query.items()}, "sslmode": sslmode},
    }
