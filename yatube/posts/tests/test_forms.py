from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User, Follow


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': "Новый пост",
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.order_by('-id')[0]
        self.assertTrue(
            post.text == form_data['text']
            and post.group_id == form_data['group']
        )

    def test_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        post = Post.objects.get(id=self.post.id)
        self.assertTrue(
            post.text == form_data['text']
            and post.group_id == form_data['group']
        )

    def test_create_post_anonymous(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': "Анонимный пост",
            'group': self.group.id,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)
        post = Post.objects.order_by('-id')[0]
        self.assertFalse(
            post.text == form_data['text']
            and post.group_id == form_data['group']
        )

    def test_edit_post_anonymous(self):
        form_data = {
            'text': "Редактирование поста",
            'group': self.group.id,
        }
        response = self.client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            f"/auth/login/?next=/posts/{self.post.id}/edit/"
        )
        post = Post.objects.get(id=self.post.id)
        self.assertFalse(
            post.text == form_data['text']
            and post.group_id == form_data['group']
        )

    def test_post_image(self):
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
        posts_count = Post.objects.count()
        form_data = {
            'text': "Пост с картинкой",
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.order_by('-id')[0]
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username})
        )
        self.assertTrue(
            post.text == form_data['text']
            and post.group_id == form_data['group']
        )
        self.assertTrue(
            form_data['image'].name.split('.')[0] in post.image.name
        )

    def test_subscribe_user(self):
        author = User.objects.create_user(username='author')
        Follow.objects.create(user=self.user, author=author)
        follow = Follow.objects.filter(user=self.user)[0]
        self.assertEqual(follow.author, author)
        Follow.objects.filter(user=self.user).delete()
        self.assertFalse(Follow.objects.filter(user=self.user).exists())
