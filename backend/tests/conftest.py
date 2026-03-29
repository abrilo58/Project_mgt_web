import os
import tempfile

import pytest


def pytest_configure(config):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DB_PATH"] = path
    os.environ["SKIP_DEMO_CARDS"] = "1"


@pytest.fixture(scope="session", autouse=True)
def _init_db_once():
    from database import init_database

    init_database()


@pytest.fixture(autouse=True)
def reset_db_and_sessions():
    import auth
    import chat_store
    from database import connect, reset_for_testing

    chat_store.clear_all()
    auth.sessions.clear()
    conn = connect()
    reset_for_testing(conn)
    conn.close()
    yield
