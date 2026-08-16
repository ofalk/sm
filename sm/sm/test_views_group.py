from django.test import TestCase, override_settings
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone

from .models import Invitation
from .utils_permissions import APP_MODELS

PASSWORD = "password123"

FAST_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class GroupMemberManagementTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Team A")
        self.owner = User.objects.create_user("owner", password=PASSWORD)
        self.member = User.objects.create_user("member", password=PASSWORD)
        self.other = User.objects.create_user("other", password=PASSWORD)

        self.group.profile.owner = self.owner
        self.group.profile.max_users = 10
        self.group.profile.save()
        self.group.user_set.add(self.owner, self.member)

        self.client.login(username="owner", password=PASSWORD)

    def test_member_list_shows_groups(self):
        response = self.client.get(reverse("group_member_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Team A")
        self.assertContains(response, "owner")
        self.assertContains(response, "member")

    def test_non_owner_cannot_add_to_foreign_group(self):
        # A non-owner cannot manage a group they don't own (404 at object level).
        self.client.logout()
        self.client.login(username="other", password=PASSWORD)
        response = self.client.post(
            reverse("group_member_add", args=[self.group.pk]),
            {"username": "owner"},
        )
        self.assertEqual(response.status_code, 404)

    def test_add_member_by_username(self):
        response = self.client.post(
            reverse("group_member_add", args=[self.group.pk]),
            {"username": "other"},
        )
        self.assertRedirects(response, reverse("group_member_list"))
        self.assertIn(self.other, self.group.user_set.all())

    def test_add_member_by_email(self):
        self.other.email = "other@example.com"
        self.other.save()
        response = self.client.post(
            reverse("group_member_add", args=[self.group.pk]),
            {"username": "other@example.com"},
        )
        self.assertRedirects(response, reverse("group_member_list"))
        self.assertIn(self.other, self.group.user_set.all())

    def test_add_unknown_user_fails(self):
        response = self.client.post(
            reverse("group_member_add", args=[self.group.pk]),
            {"username": "ghost"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User does not exist")

    def test_add_member_respects_user_quota(self):
        self.group.profile.max_users = 2  # owner + member already
        self.group.profile.save()
        response = self.client.post(
            reverse("group_member_add", args=[self.group.pk]),
            {"username": "other"},
        )
        self.assertContains(response, "User quota exceeded")
        self.assertNotIn(self.other, self.group.user_set.all())

    def test_remove_member(self):
        response = self.client.post(
            reverse("group_member_remove", args=[self.group.pk, self.member.pk])
        )
        self.assertRedirects(response, reverse("group_member_list"))
        self.assertNotIn(self.member, self.group.user_set.all())

    def test_cannot_remove_self(self):
        response = self.client.post(
            reverse("group_member_remove", args=[self.group.pk, self.owner.pk])
        )
        self.assertRedirects(response, reverse("group_member_list"))
        self.assertIn(self.owner, self.group.user_set.all())

    def test_cannot_remove_from_other_group(self):
        other_group = Group.objects.create(name="Other Team")
        response = self.client.post(
            reverse("group_member_remove", args=[other_group.pk, self.other.pk])
        )
        self.assertEqual(response.status_code, 404)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class GroupCreateAndFilterTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("creator", password=PASSWORD)
        self.client.login(username="creator", password=PASSWORD)

    def test_group_create(self):
        response = self.client.post(
            reverse("group_create"), {"name": "New Team", "max_users": 5}
        )
        self.assertRedirects(response, reverse("group_member_list"))
        group = Group.objects.get(name="New Team")
        self.assertEqual(group.profile.owner, self.user)
        self.assertEqual(group.profile.max_users, 5)
        self.assertIn(self.user, group.user_set.all())

    def test_group_create_duplicate_name(self):
        Group.objects.create(name="Taken")
        self.client.post(reverse("group_create"), {"name": "Taken", "max_users": 5})
        self.assertEqual(Group.objects.filter(name="Taken").count(), 1)

    def test_group_create_limited_to_five(self):
        for i in range(5):
            g = Group.objects.create(name=f"G{i}")
            g.profile.owner = self.user
            g.profile.save()
            self.user.groups.add(g)
        self.client.post(reverse("group_create"), {"name": "Too Many", "max_users": 5})
        self.assertEqual(Group.objects.filter(name="Too Many").count(), 0)

    def test_group_filter_sets_session(self):
        response = self.client.post(reverse("group_filter"), {"groups": "1,2,3"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["selected_groups"], ["1", "2", "3"])

    def test_group_filter_clears_session(self):
        self.client.post(reverse("group_filter"), {"groups": "1"})
        response = self.client.post(reverse("group_filter"), {"groups": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["selected_groups"], [])

    def test_group_filter_requires_auth(self):
        self.client.logout()
        response = self.client.post(reverse("group_filter"), {"groups": "1"})
        self.assertEqual(response.status_code, 401)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class GroupPermissionFormTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Perm Group")
        self.owner = User.objects.create_user("permowner", password=PASSWORD)
        self.group.profile.owner = self.owner
        self.group.profile.save()
        self.client.login(username="permowner", password=PASSWORD)

    def test_form_covers_all_12_models(self):
        from .views_group import GroupPermissionForm

        form = GroupPermissionForm(group=self.group)
        app_labels = {a for a, _ in APP_MODELS}
        field_labels = {
            f.replace("edit_", "") for f in form.fields if f.startswith("edit_")
        }
        self.assertEqual(app_labels, field_labels)

    def test_toggle_edit_permission(self):
        ct = ContentType.objects.get(app_label="cluster", model="model")
        from django.contrib.auth.models import Permission

        change_perm = Permission.objects.get(content_type=ct, codename="change_model")
        response = self.client.post(
            reverse("group_permission_edit", args=[self.group.pk]),
            {"edit_cluster": True},
        )
        self.assertRedirects(response, reverse("group_member_list"))
        self.assertIn(change_perm, self.group.permissions.all())

    def test_toggle_edit_permission_off(self):
        ct = ContentType.objects.get(app_label="status", model="model")
        from django.contrib.auth.models import Permission

        change_perm = Permission.objects.get(content_type=ct, codename="change_model")
        self.group.permissions.add(change_perm)
        response = self.client.post(
            reverse("group_permission_edit", args=[self.group.pk]),
            {"edit_status": False},
        )
        self.assertRedirects(response, reverse("group_member_list"))
        self.assertNotIn(change_perm, self.group.permissions.all())


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class InvitationFlowTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Invite Group")
        self.owner = User.objects.create_user("inviteowner", password=PASSWORD)
        self.group.profile.owner = self.owner
        self.group.profile.save()
        self.client.login(username="inviteowner", password=PASSWORD)

    def test_invite_by_email(self):
        response = self.client.post(
            reverse("group_member_invite", args=[self.group.pk]),
            {"email": "newbie@example.com"},
        )
        self.assertRedirects(response, reverse("group_member_list"))
        self.assertTrue(
            Invitation.objects.filter(
                email="newbie@example.com", group=self.group
            ).exists()
        )

    def test_duplicate_active_invitation_blocked(self):
        Invitation.objects.create(
            email="dup@example.com", group=self.group, created_by=self.owner
        )
        response = self.client.post(
            reverse("group_member_invite", args=[self.group.pk]),
            {"email": "dup@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Invitation.objects.filter(email="dup@example.com").count(), 1)

    def test_reinvite_after_expiry_replaces(self):
        old = Invitation.objects.create(
            email="again@example.com", group=self.group, created_by=self.owner
        )
        old.created_at = timezone.now() - timezone.timedelta(hours=48)
        old.save()
        response = self.client.post(
            reverse("group_member_invite", args=[self.group.pk]),
            {"email": "again@example.com"},
        )
        self.assertRedirects(response, reverse("group_member_list"))
        # No IntegrityError, exactly one invitation remains and it's fresh.
        invites = Invitation.objects.filter(email="again@example.com")
        self.assertEqual(invites.count(), 1)
        self.assertGreater(invites.first().created_at, old.created_at)

    def test_accept_invitation_creates_user_and_joins(self):
        inv = Invitation.objects.create(
            email="accept@example.com", group=self.group, created_by=self.owner
        )
        self.client.logout()
        response = self.client.post(
            reverse("accept_invitation", args=[inv.token]),
            {
                "username": "accepter",
                "email": "accept@example.com",
                "password": "s3cret-pass",
                "password_confirm": "s3cret-pass",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(username="accepter")
        self.assertIn(self.group, user.groups.all())
        inv.refresh_from_db()
        self.assertIsNotNone(inv.accepted_at)

    def test_accept_invitation_expired(self):
        inv = Invitation.objects.create(
            email="late@example.com", group=self.group, created_by=self.owner
        )
        inv.created_at = timezone.now() - timezone.timedelta(hours=48)
        inv.save()
        self.client.logout()
        response = self.client.get(reverse("accept_invitation", args=[inv.token]))
        self.assertContains(response, "expired")

    def test_accept_invitation_password_mismatch(self):
        inv = Invitation.objects.create(
            email="mismatch@example.com", group=self.group, created_by=self.owner
        )
        self.client.logout()
        response = self.client.post(
            reverse("accept_invitation", args=[inv.token]),
            {
                "username": "mismatch",
                "email": "mismatch@example.com",
                "password": "one",
                "password_confirm": "two",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="mismatch").exists())
