import unittest
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from config.database import build_database_settings


class DatabaseSettingsTests(unittest.TestCase):
    def test_debug_defaults_to_local_sqlite(self):
        self.assertEqual(
            build_database_settings(None, True, Path("local.sqlite3")),
            {"ENGINE": "django.db.backends.sqlite3", "NAME": Path("local.sqlite3")},
        )

    def test_production_requires_postgres(self):
        with self.assertRaisesRegex(ImproperlyConfigured, "DATABASE_URL"):
            build_database_settings(None, False, Path("local.sqlite3"))

    def test_parses_postgres_credentials_and_tls(self):
        config = build_database_settings(
            "postgresql://school:pa%24%24@db.example:5433/campusflow?sslmode=verify-full&connect_timeout=5",
            False,
            Path("local.sqlite3"),
        )
        self.assertEqual(config["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual((config["NAME"], config["USER"], config["PASSWORD"]), ("campusflow", "school", "pa$$"))
        self.assertEqual((config["HOST"], config["PORT"]), ("db.example", "5433"))
        self.assertEqual(config["OPTIONS"], {"sslmode": "verify-full", "connect_timeout": "5"})

    def test_production_rejects_insecure_or_unsupported_urls(self):
        for url in (
            "postgres://school:secret@db.example/campusflow?sslmode=disable",
            "postgres://db.example/campusflow?sslmode=require",
            "sqlite:///campusflow.sqlite3",
            "postgres://school:secret@db.example",
        ):
            with self.subTest(url=url), self.assertRaises(ImproperlyConfigured):
                build_database_settings(url, False, Path("local.sqlite3"))


if __name__ == "__main__":
    unittest.main()
