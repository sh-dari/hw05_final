from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

import shutil
import tempfile

from posts.models import Group, Post, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        pages_names = {
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username})
        }
        for field in pages_names:
            with self.subTest(field=field):
                response = self.authorized_client.get(field)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, self.post.text)
                self.assertEqual(first_object.group, self.group)
                self.assertEqual(first_object.id, self.post.id)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug})
        )
        group = response.context['group']
        self.assertEqual(group, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username})
        )
        author = response.context['author']
        self.assertEqual(author, self.user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})
        )
        post = response.context['post']
        self.assertEqual(post, self.post)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_group_show(self):
        self.new_group = Group.objects.create(
            title='Новая группа',
            slug='new_slug',
            description='Новое описание'
        )
        self.new_post = Post.objects.create(
            author=User.objects.get(username='auth'),
            text='Новая запись',
            group=self.new_group
        )
        templates_pages_names = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.new_group.slug}),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username})
        ]
        for template in templates_pages_names:
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                first_post = response.context['page_obj'][0]
                self.assertEqual(self.new_post.text, first_post.text)

    def test_new_post_author_show(self):
        new_post_author = Post.objects.create(
            author=User.objects.get(username='auth'),
            text='Запись автора',
            group=self.group
        )
        follow = User.objects.create_user(username='follow')
        follow_client = Client()
        follow_client.force_login(follow)
        unfollow = User.objects.create_user(username='unfollow')
        unfollow_client = Client()
        unfollow_client.force_login(unfollow)
        Follow.objects.create(user=follow, author=self.user)
        response = follow_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(new_post_author.text, post.text)
        response = unfollow_client.get(reverse('posts:follow_index'))
        self.assertTrue(len(response.context['page_obj']) == 0)

    def test_follow_user(self):
        follow = User.objects.create_user(username='follow')
        follow_client = Client()
        follow_client.force_login(follow)
        follow_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}
        ))
        self.assertTrue(Follow.objects.filter(
            author=self.user,
            user=follow
        ).exists())

    def test_unfollow_user(self):
        follow = User.objects.create_user(username='follow')
        follow_client = Client()
        follow_client.force_login(follow)
        Follow.objects.create(author=self.user, user=follow)
        follow_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user.username}
        ))
        self.assertFalse(Follow.objects.filter(
            author=self.user,
            user=follow
        ).exists())


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        for _ in range(13):
            Post.objects.create(
                author=cls.user,
                text='Текст',
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        templates_pages_names = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username})
        ]
        for template in templates_pages_names:
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.PAGE_SIZE
                )

    def test_second_page_contains_three_records(self):
        templates_pages_names = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username})
        ]
        count_posts = Post.objects.all().count() - settings.PAGE_SIZE
        for template in templates_pages_names:
            response = self.authorized_client.get(
                template + '?page=2'
            )
            self.assertEqual(len(response.context['page_obj']), count_posts)
