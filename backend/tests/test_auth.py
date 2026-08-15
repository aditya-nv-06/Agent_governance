import os
import tempfile
import unittest
import uuid

_DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_DB_FILE.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE.name}"
os.environ["ALLOW_SQLITE_FOR_TESTS"] = "true"

from fastapi import HTTPException

from app.database import Base, SessionLocal, engine
from app.models import AdminUser
from app.routes.agents import create_agent
from app.routes.auth import login, register
from app.schemas import AdminLoginRequest, AdminRegisterRequest, AgentCreate


class AuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(engine)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_admin_can_register_and_login(self):
        email = f"admin-{uuid.uuid4()}@example.com"
        registered = register(AdminRegisterRequest(email=email, password="secure-password"), self.db)
        self.assertTrue(registered.access_token)
        self.assertEqual(registered.admin.role, "admin")

        logged_in = login(AdminLoginRequest(email=email, password="secure-password"), self.db)
        self.assertTrue(logged_in.access_token)

    def test_login_rejects_invalid_password(self):
        email = f"admin-{uuid.uuid4()}@example.com"
        register(AdminRegisterRequest(email=email, password="secure-password"), self.db)
        with self.assertRaises(HTTPException) as error:
            login(AdminLoginRequest(email=email, password="wrong-password"), self.db)
        self.assertEqual(error.exception.status_code, 401)

    def test_agent_creation_requires_profile(self):
        email = f"admin-{uuid.uuid4()}@example.com"
        admin = AdminUser(
            email=email,
            password_hash="hash",
            password_salt="salt",
            role="admin",
        )
        self.db.add(admin)
        self.db.commit()

        with self.assertRaises(HTTPException) as error:
            create_agent(AgentCreate(name="No profile agent", description="This should be rejected"), self.db, admin)

        self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
