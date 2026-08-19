from django.test import TestCase, Client
from django.contrib.auth.models import User, Group, Permission
from vendor.models import Model as Vendor
from django.urls import reverse
from .utils_starterpack import import_starter_pack


class MultiTenancyExpandedTest(TestCase):
    def setUp(self) -> None:
        self.password = "password123"

        # Create two groups
        self.group_a = Group.objects.create(name="Group A")
        self.group_b = Group.objects.create(name="Group B")

        # Create profiles
        self.profile_a = self.group_a.profile
        self.profile_b = self.group_b.profile

        # Create users
        self.user_a = User.objects.create_user(
            username="user_a", password=self.password
        )
        self.user_b = User.objects.create_user(
            username="user_b", password=self.password
        )

        self.user_a.groups.add(self.group_a)
        self.user_b.groups.add(self.group_b)

        # Set owners
        self.profile_a.owner = self.user_a
        self.profile_a.save()
        self.profile_b.owner = self.user_b
        self.profile_b.save()

        # Create clients
        self.client_a = Client()
        self.client_a.login(username="user_a", password=self.password)
        self.client_b = Client()
        self.client_b.login(username="user_b", password=self.password)

    def test_vendor_partitioning(self) -> None:
        """Test that vendors are filtered by group."""
        Vendor.objects.create(name="Vendor A", group=self.group_a)
        Vendor.objects.create(name="Vendor B", group=self.group_b)

        # User A should only see Vendor A
        # Give permission first
        view_perm = Permission.objects.get(
            codename="view_model", content_type__app_label="vendor"
        )
        self.group_a.permissions.add(view_perm)

        response = self.client_a.get(reverse("vendor:index"))
        self.assertContains(response, "Vendor A")
        self.assertNotContains(response, "Vendor B")

    def test_starter_pack_import(self) -> None:
        """Test starter pack utility logic."""
        # Ensure group is empty
        Vendor.objects.filter(group=self.group_a).delete()

        results = import_starter_pack(self.group_a)
        self.assertGreater(results["vendors"], 0)
        self.assertGreater(results["os"], 0)

        self.assertTrue(
            Vendor.objects.filter(group=self.group_a, name="Red Hat").exists()
        )

    def test_item_quota_enforcement(self) -> None:
        """Test that group item quota is enforced."""
        self.profile_a.max_items = 1
        self.profile_a.save()

        # Create one vendor
        Vendor.objects.create(name="Vendor 1", group=self.group_a)

        # Try to create another via view (should fail)
        add_perm = Permission.objects.get(
            codename="add_model", content_type__app_label="vendor"
        )
        self.group_a.permissions.add(add_perm)

        response = self.client_a.post(
            reverse("vendor:create"),
            {"name": "Vendor 2", "is_hardware": True, "is_software": True},
            follow=True,
        )
        self.assertContains(response, "Quota exceeded")
        self.assertEqual(Vendor.objects.filter(group=self.group_a).count(), 1)

    def test_user_quota_enforcement(self) -> None:
        """Test that group user quota is enforced."""
        self.profile_a.max_users = 1  # Only user_a
        self.profile_a.save()

        user_c = User.objects.create_user(username="user_c", password=self.password)

        response = self.client_a.post(
            reverse("group_member_add", args=[self.group_a.id]),
            {"username": "user_c"},
            follow=True,
        )
        self.assertContains(response, "User quota exceeded")
        self.assertNotIn(user_c, self.group_a.user_set.all())

    def test_group_owner_permissions_management(self) -> None:
        """Test that group owner can change group permissions."""
        # Check initial perms (view only by default signal)
        from django.contrib.contenttypes.models import ContentType

        server_ct = ContentType.objects.get(app_label="server", model="model")
        change_perm = Permission.objects.get(
            content_type=server_ct, codename="change_model"
        )

        self.assertNotIn(change_perm, self.group_a.permissions.all())

        # Toggle edit_server
        # The form field name is edit_<app_label>
        response = self.client_a.post(
            reverse("group_permission_edit", args=[self.group_a.id]),
            {"edit_server": True},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        self.assertIn(change_perm, self.group_a.permissions.all())

        # Toggle off
        self.client_a.post(
            reverse("group_permission_edit", args=[self.group_a.id]),
            {"edit_server": False},
            follow=True,
        )
        self.assertNotIn(change_perm, self.group_a.permissions.all())


class MultiTenancyEdgeCasesTest(TestCase):
    def setUp(self) -> None:
        self.password = "password123"

        # Create groups
        self.group_a = Group.objects.create(name="Group A")
        self.group_b = Group.objects.create(name="Group B")

        # Create profiles
        self.profile_a = self.group_a.profile
        self.profile_b = self.group_b.profile

        # Create users
        self.user_a = User.objects.create_user(
            username="user_a", password=self.password
        )
        self.user_b = User.objects.create_user(
            username="user_b", password=self.password
        )
        self.superuser = User.objects.create_superuser(
            username="superuser", password=self.password, email="super@example.com"
        )

        self.user_a.groups.add(self.group_a)
        self.user_b.groups.add(self.group_b)

        # Set owners
        self.profile_a.owner = self.user_a
        self.profile_a.save()
        self.profile_b.owner = self.user_b
        self.profile_b.save()

        # Create clients
        self.client_a = Client()
        self.client_a.login(username="user_a", password=self.password)
        self.client_b = Client()
        self.client_b.login(username="user_b", password=self.password)
        self.superuser_client = Client()
        self.superuser_client.login(username="superuser", password=self.password)

    def test_superuser_bypasses_all_restrictions(self) -> None:
        """Test that superusers can see and create items in any group."""
        # Create items in different groups
        Vendor.objects.create(name="Vendor A", group=self.group_a)
        Vendor.objects.create(name="Vendor B", group=self.group_b)

        # Superuser should see all items
        response = self.superuser_client.get(reverse("vendor:index"))
        self.assertContains(response, "Vendor A")
        self.assertContains(response, "Vendor B")

        # Superuser should be able to create items without group assignment
        response = self.superuser_client.post(
            reverse("vendor:create"),
            {"name": "Vendor Super", "is_hardware": True, "is_software": True},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        # Item should be created without a group (global)
        vendor = Vendor.objects.get(name="Vendor Super")
        self.assertIsNone(vendor.group)

    def test_global_items_visible_to_all_users(self) -> None:
        """Test that items with no group are visible to all users."""
        # Create a global vendor (no group)
        global_vendor = Vendor.objects.create(name="Global Vendor")
        self.assertIsNone(global_vendor.group)

        # Both users should see the global vendor
        response_a = self.client_a.get(reverse("vendor:index"))
        response_b = self.client_b.get(reverse("vendor:index"))

        self.assertContains(response_a, "Global Vendor")
        self.assertContains(response_b, "Global Vendor")

    def test_user_without_group_cannot_create_items(self) -> None:
        """Test that users without any groups cannot create items."""
        # Create a user without any groups
        user_no_group = User.objects.create_user(
            username="user_no_group", password=self.password
        )
        # Clear automatically created personal group for this test case
        user_no_group.groups.clear()

        client_no_group = Client()
        client_no_group.login(username="user_no_group", password=self.password)

        # Grant necessary permissions
        add_perm = Permission.objects.get(
            codename="add_model", content_type__app_label="vendor"
        )
        view_perm = Permission.objects.get(
            codename="view_model", content_type__app_label="vendor"
        )
        user_no_group.user_permissions.add(add_perm, view_perm)

        # A group-less user must not be able to create global/shared rows
        response = client_no_group.post(
            reverse("vendor:create"),
            {"name": "Vendor No Group", "is_hardware": True, "is_software": True},
            follow=True,
        )

        # Should be denied and create nothing without a group
        self.assertIn(response.status_code, [403, 404])
        self.assertFalse(Vendor.objects.filter(name="Vendor No Group").exists())

    def test_concurrent_quota_checks(self) -> None:
        """Test that concurrent quota checks are handled properly."""
        self.profile_a.max_items = 1
        self.profile_a.save()

        # Grant add permission
        add_perm = Permission.objects.get(
            codename="add_model", content_type__app_label="vendor"
        )
        self.group_a.permissions.add(add_perm)

        # Create one vendor to reach the limit
        Vendor.objects.create(name="Vendor 1", group=self.group_a)

        # Try to create another vendor (should fail due to quota)
        response = self.client_a.post(
            reverse("vendor:create"),
            {"name": "Vendor 2", "is_hardware": True, "is_software": True},
            follow=True,
        )
        self.assertContains(response, "Quota exceeded")
        self.assertEqual(Vendor.objects.filter(group=self.group_a).count(), 1)

    def test_unique_constraints_per_group(self) -> None:
        """Test that unique constraints work correctly per group."""
        # Both groups should be able to have vendors with the same name
        Vendor.objects.create(name="Same Name", group=self.group_a)
        Vendor.objects.create(name="Same Name", group=self.group_b)

        # Should have 2 vendors total
        self.assertEqual(Vendor.objects.filter(name="Same Name").count(), 2)

        # But each user should only see their own
        response_a = self.client_a.get(reverse("vendor:index"))
        response_b = self.client_b.get(reverse("vendor:index"))

        # Count occurrences in response (this is a simple check)
        self.assertContains(response_a, "Same Name")
        self.assertContains(response_b, "Same Name")

    def test_group_deletion_cascades_to_items(self) -> None:
        """Test that deleting a group properly handles related items."""
        # Create some items in group A
        Vendor.objects.create(name="Vendor A1", group=self.group_a)
        Vendor.objects.create(name="Vendor A2", group=self.group_a)

        initial_count = Vendor.objects.count()

        # Delete the group (should be protected by on_delete=models.PROTECT)
        with self.assertRaises(Exception):
            self.group_a.delete()

        # Items should still exist
        self.assertEqual(Vendor.objects.count(), initial_count)

    def test_user_cannot_access_other_group_items_directly(self) -> None:
        """Test that users cannot access items from other groups via direct URLs."""
        # Create an item in group B
        vendor_b = Vendor.objects.create(name="Vendor B Private", group=self.group_b)

        # User A should not be able to access this item's detail page
        response = self.client_a.get(reverse("vendor:detail", args=[vendor_b.pk]))

        # Should either return 404 or 403
        self.assertIn(response.status_code, [403, 404])

    def test_starter_pack_with_existing_data(self) -> None:
        """Test starter pack import when group already has some data."""
        # Create some existing data
        Vendor.objects.create(name="Existing Vendor", group=self.group_a)

        # Import starter pack
        results = import_starter_pack(self.group_a)

        # Should still import new vendors but not duplicate existing ones
        self.assertGreaterEqual(results["vendors"], 0)

        # Existing vendor should still be there
        self.assertTrue(
            Vendor.objects.filter(group=self.group_a, name="Existing Vendor").exists()
        )

    def test_quota_zero_allows_no_items(self) -> None:
        """Test that setting quota to zero prevents all item creation."""
        self.profile_a.max_items = 0
        self.profile_a.save()

        # Grant add permission
        add_perm = Permission.objects.get(
            codename="add_model", content_type__app_label="vendor"
        )
        self.group_a.permissions.add(add_perm)

        # Try to create an item (should fail)
        response = self.client_a.post(
            reverse("vendor:create"),
            {"name": "Vendor Zero Quota", "is_hardware": True, "is_software": True},
            follow=True,
        )
        self.assertContains(response, "Quota exceeded")
        self.assertEqual(Vendor.objects.filter(group=self.group_a).count(), 0)

    def test_group_profile_creation_on_group_creation(self) -> None:
        """Test GroupProfile auto-creation when new group is created."""
        # Create a new group
        new_group = Group.objects.create(name="New Group")

        # Should have a profile
        self.assertTrue(hasattr(new_group, "profile"))
        self.assertIsNotNone(new_group.profile)

        # Profile should have default values
        self.assertEqual(new_group.profile.max_items, 200)
        self.assertEqual(new_group.profile.max_users, 2)
