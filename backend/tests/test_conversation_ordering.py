import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Session

import app.db.base  # noqa: F401
from app.crud.conversation import list_by_store, list_by_user
from app.db.session import SessionLocal


class ConversationOrderingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        SessionLocal.configure(bind=self.engine)
        self.session = Session(self.engine)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_list_by_store_uses_mysql_safe_null_ordering(self) -> None:
        captured = {}

        def fake_all(query):
            compiled = query.statement.compile(
                dialect=mysql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
            captured["sql"] = str(compiled)
            return []

        with patch("sqlalchemy.orm.query.Query.all", autospec=True, side_effect=fake_all):
            list_by_store(self.session, "store-1")

        sql = captured["sql"]
        self.assertNotIn("NULLS LAST", sql)
        self.assertIn("conversations.last_message_at IS NULL", sql)

    def test_list_by_user_uses_mysql_safe_null_ordering(self) -> None:
        captured = {}

        def fake_all(query):
            compiled = query.statement.compile(
                dialect=mysql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
            captured["sql"] = str(compiled)
            return []

        with patch("sqlalchemy.orm.query.Query.all", autospec=True, side_effect=fake_all):
            list_by_user(self.session, "user-1")

        sql = captured["sql"]
        self.assertNotIn("NULLS LAST", sql)
        self.assertIn("conversations.last_message_at IS NULL", sql)


if __name__ == "__main__":
    unittest.main()
