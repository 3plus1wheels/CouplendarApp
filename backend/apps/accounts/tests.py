from rest_framework import status
from rest_framework.test import APITestCase


class AuthEndpointsTests(APITestCase):
    def test_register_login_me_and_profile_patch(self):
        register_payload = {
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "display_name": "Hoang",
        }
        register_response = self.client.post("/api/auth/register/", register_payload, format="json")
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", register_response.data)
        self.assertIn("refresh", register_response.data)
        self.assertEqual(register_response.data["user"]["email"], "test@example.com")

        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "test@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        access = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        me_response = self.client.get("/api/auth/me/")
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["email"], "test@example.com")

        profile_patch = self.client.patch(
            "/api/profile/",
            {"city": "Calgary", "first_name": "Test"},
            format="json",
        )
        self.assertEqual(profile_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_patch.data["city"], "Calgary")
        self.assertEqual(profile_patch.data["first_name"], "Test")
