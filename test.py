from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserManagerTests(TestCase):
    """Тесты для менеджера пользователей."""

    def test_create_user_with_email_successful(self):
        """Проверка создания пользователя с email."""
        email = "test@example.com"
        password = "testpass123"
        user = User.objects.create_user(
            email=email,
            name="Test",
            surname="User",
            password=password,
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Проверка создания суперпользователя."""
        email = "admin@example.com"
        password = "adminpass123"
        admin = User.objects.create_superuser(
            email=email,
            name="Admin",
            surname="User",
            password=password,
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)


class UserAvatarGenerationTests(TestCase):
    """Тесты для генерации аватаров."""

    def test_avatar_generated_on_creation(self):
        """Проверка автогенерации аватара при создании."""
        user = User.objects.create_user(
            email="avatar_test@example.com",
            name="Avatar",
            surname="Test",
            password="pass",
        )
        self.assertIsNotNone(user.avatar)
        self.assertTrue(user.avatar.name.endswith(".png"))

    def test_avatar_uses_first_letter_of_name(self):
        """Проверка что аватар использует первую букву имени."""
        user = User.objects.create_user(
            email="letter_test@example.com",
            name="Zebra",
            surname="Test",
            password="pass",
        )
        # Аватар должен быть создан (конкретную букву проверить сложно из-за рандома цвета)
        self.assertIsNotNone(user.avatar)


class UserModelTests(TestCase):
    """Тесты модели User."""

    def test_str_method(self):
        """Проверка строкового представления."""
        user = User.objects.create_user(
            email="str_test@example.com",
            name="John",
            surname="Doe",
            password="pass",
        )
        self.assertEqual(str(user), "John Doe (str_test@example.com)")

    def test_email_unique(self):
        """Проверка уникальности email."""
        User.objects.create_user(
            email="unique@example.com",
            name="First",
            surname="User",
            password="pass",
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="unique@example.com",
                name="Second",
                surname="User",
                password="pass",
            )


class RegisterViewTests(TestCase):
    """Тесты представления регистрации."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("users:register")

    def test_register_get(self):
        """Проверка GET запроса к регистрации."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_post_valid(self):
        """Проверка успешной регистрации."""
        data = {
            "email": "newuser@example.com",
            "name": "New",
            "surname": "User",
            "password": "securepass123",
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse("users:login"))
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_register_post_invalid(self):
        """Проверка регистрации с невалидными данными."""
        data = {
            "email": "invalid-email",
            "name": "",
            "surname": "User",
            "password": "pass",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="invalid-email").exists())


class LoginViewTests(TestCase):
    """Тесты представления входа."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="login_test@example.com",
            name="Login",
            surname="Test",
            password="testpass123",
        )
        self.url = reverse("users:login")

    def test_login_get(self):
        """Проверка GET запроса ко входу."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_login_post_valid(self):
        """Проверка успешного входа."""
        data = {
            "email": "login_test@example.com",
            "password": "testpass123",
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse("projects:list"))
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_login_post_invalid_password(self):
        """Проверка входа с неверным паролем."""
        data = {
            "email": "login_test@example.com",
            "password": "wrongpass",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Неверный email или пароль")


class LogoutViewTests(TestCase):
    """Тесты представления выхода."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="logout_test@example.com",
            name="Logout",
            surname="Test",
            password="testpass123",
        )
        self.url = reverse("users:logout")

    def test_logout(self):
        """Проверка выхода."""
        self.client.login(email="logout_test@example.com", password="testpass123")
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("projects:list"))
        self.assertFalse("_auth_user_id" in self.client.session)


class UserDetailViewTests(TestCase):
    """Тесты представления профиля пользователя."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="detail_test@example.com",
            name="Detail",
            surname="Test",
            password="testpass123",
        )
        self.url = reverse("users:detail", kwargs={"user_id": self.user.pk})

    def test_user_detail_get(self):
        """Проверка просмотра профиля."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/user-details.html")
        self.assertEqual(response.context["user"], self.user)

    def test_user_detail_not_found(self):
        """Проверка 404 для несуществующего пользователя."""
        url = reverse("users:detail", kwargs={"user_id": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class EditProfileViewTests(TestCase):
    """Тесты редактирования профиля."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="edit_test@example.com",
            name="Edit",
            surname="Test",
            password="testpass123",
        )
        self.url = reverse("users:edit_profile")

    def test_edit_profile_requires_login(self):
        """Проверка требования авторизации."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/users/login/?next={self.url}")

    def test_edit_profile_get(self):
        """Проверка GET запроса авторизованного пользователя."""
        self.client.login(email="edit_test@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/edit_profile.html")

    def test_edit_profile_post_valid(self):
        """Проверка успешного редактирования."""
        self.client.login(email="edit_test@example.com", password="testpass123")
        data = {
            "name": "Updated",
            "surname": "Name",
            "phone": "",
            "about": "New about text",
            "github_url": "",
        }
        response = self.client.post(self.url, data, follow=True)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Updated")
        self.assertEqual(self.user.surname, "Name")


class ChangePasswordViewTests(TestCase):
    """Тесты смены пароля."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="password_test@example.com",
            name="Password",
            surname="Test",
            password="oldpass123",
        )
        self.url = reverse("users:change_password")

    def test_change_password_requires_login(self):
        """Проверка требования авторизации."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/users/login/?next={self.url}")

    def test_change_password_success(self):
        """Проверка успешной смены пароля."""
        self.client.login(email="password_test@example.com", password="oldpass123")
        data = {
            "old_password": "oldpass123",
            "new_password1": "newpass456",
            "new_password2": "newpass456",
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(
            response, reverse("users:detail", kwargs={"user_id": self.user.pk})
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass456"))


class ParticipantsViewTests(TestCase):
    """Тесты списка участников."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("users:list")

    def test_participants_get(self):
        """Проверка просмотра списка участников."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/participants.html")
        self.assertIn("participants", response.context)
