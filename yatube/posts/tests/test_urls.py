from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client

from http import HTTPStatus

from ..models import Group, Post


User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exists_at_desired_location(self):
        urls = [
            "/",
            f"/group/{self.group.slug}/",
            f"/profile/{self.user.username}/",
            f"/posts/{self.post.id}/",
        ]
        for field in urls:
            with self.subTest(field=field):
                self.assertEqual(
                    self.client.get(field).status_code, HTTPStatus.OK)

    def test_url_exists_authorized_client(self):
        urls = [
            f"/posts/{self.post.id}/edit/",
            "/create/",
        ]
        for field in urls:
            with self.subTest(field=field):
                response = self.authorized_client.get(field)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_if_anonymous(self):
        urls = [
            f"/posts/{self.post.id}/edit/",
            "/create/",
        ]
        for field in urls:
            with self.subTest(field=field):
                response = self.client.get(field)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f"/group/{self.group.slug}/": 'posts/group_list.html',
            f"/profile/{self.user.username}/": 'posts/profile.html',
            f"/posts/{self.post.id}/": 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f"/posts/{self.post.id}/edit/": 'posts/create_post.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def unexisting_page_error(self):
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_main_page_cache(self):
        response = self.authorized_client.get('')
        Post.objects.get(id=self.post.id).delete()
        self.assertContains(response, self.post)
        cache.clear()
        response = self.authorized_client.get('')
        self.assertNotContains(response, self.post)
