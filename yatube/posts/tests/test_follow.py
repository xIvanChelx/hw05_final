from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post

User = get_user_model()


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='follower')
        cls.user_followed = User.objects.create_user(username='followed')
        cls.post = Post.objects.create(
            author=cls.user_followed,
            text='Тестовый текст'
        )

    def setUp(self):
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(self.user_follower)
        self.authorized_client_followed = Client()
        self.authorized_client_followed.force_login(self.user_followed)

    def test_follow(self):
        """
        Авторизованный пользователь
        может подписываться на других пользователей
        и удалять их из подписок.
        """
        follows_count = Follow.objects.count()
        self.authorized_client_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_followed.username}))
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        self.authorized_client_follower.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user_followed.username}))
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_post_in_follow_page(self):
        """
        Пост появляется в ленте тех,
        кто на него подписан
        и не появляется в ленте тех,
        кто не подписан."""
        self.authorized_client_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_followed.username}))
        response_followed = self.authorized_client_follower.get(
            reverse('posts:follow_index'))
        self.assertContains(response_followed, self.post.text)
        response_unfollowed = self.authorized_client_followed.get(
            reverse('posts:follow_index'))
        self.assertNotContains(response_unfollowed, self.post.text)
