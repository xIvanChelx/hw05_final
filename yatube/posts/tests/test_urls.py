from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about(self):
        response = self.guest_client.get(reverse('about:author'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech(self):
        response = self.guest_client.get(reverse('about:tech'))
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_unauthorized_user(self):
        """Доступность страниц для неавторизованного пользователя."""

        pages = {'/': HTTPStatus.OK,
                 f'/group/{PostsUrlTest.group.slug}/': HTTPStatus.OK,
                 f'/profile/{PostsUrlTest.user.username}/': HTTPStatus.OK,
                 f'/posts/{PostsUrlTest.post.id}/': HTTPStatus.OK,
                 f'/posts/{PostsUrlTest.post.id}/edit/': HTTPStatus.FOUND,
                 '/create/': HTTPStatus.FOUND,
                 '/unexisting_page/': HTTPStatus.NOT_FOUND
                 }
        for adress, response_code in pages.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, response_code)

    def test_edit_post_authorized_user(self):
        """
        Страница редактирования поста доступна авторизованному пользователю.
        """

        response = self.authorized_client.get(
            f'/posts/{PostsUrlTest.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_authorized_user(self):
        """Страница создания поста доступна авторизованному пользователю"""

        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_templates(self):
        """URL-адреса используют правильные шаблоны."""

        url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{PostsUrlTest.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostsUrlTest.user.username}/': 'posts/profile.html',
            f'/posts/{PostsUrlTest.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostsUrlTest.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
            }
        for adress, template in url_templates_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
