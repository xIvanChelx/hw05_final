from django.core.cache import cache
from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsCacheTest(TestCase):
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

    def test_cache_index_page_correct_context(self):
        """Пост после удаления остается в кеше."""
        first_response = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(first_response, self.post.text)
        self.post.delete()
        second_response = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(second_response, self.post.text)
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotContains(third_response, self.post.text)
