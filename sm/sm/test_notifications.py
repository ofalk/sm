from django.test import TestCase, override_settings
from django.contrib.auth.models import Group, User
from django.core import mail

PASSWORD = "password123"
FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
@override_settings(
    SERVER_STATUS_NOTIFY=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class StatusChangeNotificationTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Notify Group")
        self.member = User.objects.create_user(
            "member", email="member@example.com", password=PASSWORD
        )
        self.group.user_set.add(self.member)

        from status.models import Model as Status
        from domain.models import Model as Domain
        from server.models import Model as Server

        self.in_use = Status.objects.create(name="In use")
        self.retired = Status.objects.create(name="Retired")
        self.domain = Domain.objects.create(name="notify.example.com")
        self.server = Server.objects.create(
            hostname="notifysrv",
            status=self.in_use,
            domain=self.domain,
            group=self.group,
        )

    def test_notifies_on_status_change(self):
        mail.outbox.clear()
        self.server.status = self.retired
        self.server.save()
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("member@example.com", email.to)
        self.assertIn("notifysrv", email.subject)
        self.assertIn("notifysrv", email.body)

    def test_no_notification_without_change(self):
        mail.outbox.clear()
        self.server.save()
        self.assertEqual(len(mail.outbox), 0)

    def test_no_notification_on_create(self):
        mail.outbox.clear()
        from server.models import Model as Server

        Server.objects.create(
            hostname="brandnew",
            status=self.in_use,
            domain=self.domain,
            group=self.group,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_disabled_notification_sends_nothing(self):
        from django.test.utils import override_settings as ovs

        with ovs(SERVER_STATUS_NOTIFY=False):
            mail.outbox.clear()
            self.server.status = self.retired
            self.server.save()
            self.assertEqual(len(mail.outbox), 0)
