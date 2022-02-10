from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsViewsTest(TestCase):
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
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_views_uses_correct_templates(self):
        """View-функции используют правильные шаблоны."""

        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user.username}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'}
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""

        response = (self.authorized_client.get(reverse('posts:index',)))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""

        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.group, self.post.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""

        response = (self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author.username, self.user.username)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""

        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})))
        first_object = response.context['post']
        self.assertEqual(first_object.id, self.post.id)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""

        response = (self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').group, self.post.group)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""

        response = (self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})))
        form_fields = {
            'text': forms.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_in_index_group_list_profile_pages(self):
        """
        Если при создании поста указана группа,
        пост появляется на главной странице,
        на странице выбранной группы, в профайле пользователя.
        """

        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(response, self.post.text)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertContains(response, self.post.text)
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        self.assertContains(response, self.post.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.batch_size = 13
        cls.obj_list = [Post(author=cls.user, text=f'Тестовый текст {i}',
                             group=cls.group) for i in range(cls.batch_size)]
        cls.posts_to_check = Post.objects.bulk_create(cls.obj_list)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        """Количество постов на первой странице равно 10."""

        POST_COUNT = 10
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POST_COUNT)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']), POST_COUNT)
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(len(response.context['page_obj']), POST_COUNT)

    def test_second_page_contains_three_posts(self):
        """Количество постов на второй странице равно 3."""

        POST_COUNT = 3
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), POST_COUNT)
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), POST_COUNT)
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), POST_COUNT)


class PostsViewsGroupListTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.post_2 = Post.objects.create(
            author=cls.user,
            text='Тестовый текст 2',
            group=cls.group_2,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_in_correct_group_list(self):
        """Пост не появляется в неправильной группе."""

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug}))
        self.assertNotEqual(response.context.get('post').group,
                            self.post.group)
