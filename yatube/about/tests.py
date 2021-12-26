from django.contrib.auth import get_user_model
from django.test import TestCase, Client


User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_authpage(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_techpage(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)

    def test_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(template)
                self.assertTemplateUsed(response, adress)
