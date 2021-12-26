from django.contrib.auth import get_user_model
from django.test import TestCase, Client


User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exists_at_desired_location(self):
        urls = [
            '/auth/logout/',
            '/auth/login/'
        ]
        for field in urls:
            with self.subTest(field=field):
                self.assertEqual(
                    self.authorized_client.get(field).status_code, 200)

    def test_url_signup(self):
        self.assertEqual(
            self.guest_client.get('/auth/signup/').status_code, 200)
