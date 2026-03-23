from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from sm.models import GroupProfile


class Command(BaseCommand):
    help = "Create test data with a second group and add admin to multiple groups"

    def handle(self, *args, **options):
        dummy_user, created = User.objects.get_or_create(
            username="dummyuser",
            defaults={
                "email": "dummyuser@example.com",
                "is_staff": False,
            },
        )
        if created:
            dummy_user.set_password("dummyuser123")
            dummy_user.save()
            self.stdout.write(self.style.SUCCESS("Created user: dummyuser"))

        dummy_group, created = Group.objects.get_or_create(name="dummygroup")
        if created:
            self.stdout.write(self.style.SUCCESS("Created group: dummygroup"))

        profile, _ = GroupProfile.objects.get_or_create(
            group=dummy_group,
            defaults={
                "max_users": 10,
            },
        )
        profile.owner = dummy_user
        profile.save()

        lkern_group, _ = Group.objects.get_or_create(name="lkernAT")
        GroupProfile.objects.get_or_create(
            group=lkern_group,
            defaults={"max_users": 10},
        )

        admin_user = User.objects.get(username="admin")

        if lkern_group not in admin_user.groups.all():
            admin_user.groups.add(lkern_group)
            self.stdout.write(self.style.SUCCESS("Added admin to lkernAT"))

        if dummy_group not in admin_user.groups.all():
            admin_user.groups.add(dummy_group)
            self.stdout.write(self.style.SUCCESS("Added admin to dummygroup"))

        admin_groups = list(admin_user.groups.all())
        group_names = [g.name for g in admin_groups]
        self.stdout.write(
            self.style.SUCCESS(
                f"admin is now in {len(admin_groups)} groups: {group_names}"
            )
        )

        owner = dummy_group.profile.owner
        self.stdout.write(
            self.style.SUCCESS(
                f"dummyuser owns group: {dummy_group.name} (owner: {owner})"
            )
        )
