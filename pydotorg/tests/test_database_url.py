from django.db.utils import ConnectionHandler
from django.test import SimpleTestCase
from psycopg2.extensions import make_dsn, parse_dsn

from pydotorg.settings.base import dj_database_url_parser


class DatabaseUrlParsingTests(SimpleTestCase):
    def connection_options(self, url):
        connection = ConnectionHandler({"default": dj_database_url_parser(url)})["default"]
        options = connection.get_connection_params()
        options.pop("cursor_factory")
        return parse_dsn(make_dsn(**options))

    def test_encoded_credentials_and_socket_path(self):
        options = self.connection_options("postgres://user:p%40ss%2Fw%3Ard@%2Fvar%2Frun%2Fpostgresql/pythondotorg")
        self.assertEqual(options["password"], "p@ss/w:rd")
        self.assertEqual(options["host"], "/var/run/postgresql")
        self.assertEqual(options["dbname"], "pythondotorg")

    def test_tls_and_timeout_reach_postgres(self):
        options = self.connection_options(
            "postgresql://user:pass@dbhost:5432/pythondotorg?sslmode=verify-full"
            "&sslrootcert=%2Frun%2Fsecrets%2Fca.crt&connect_timeout=30"
        )
        self.assertEqual(options["sslmode"], "verify-full")
        self.assertEqual(options["sslrootcert"], "/run/secrets/ca.crt")
        self.assertEqual(options["connect_timeout"], "30")
        self.assertEqual(options["host"], "dbhost")
        self.assertEqual(options["port"], "5432")
