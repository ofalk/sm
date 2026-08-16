from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from simple_history.admin import SimpleHistoryAdmin

from patchtime.models import Model as PatchtimeModel
from server.models import Model as ServerModel
from servermodel.models import Model as ServermodelModel
from status.models import Model as StatusModel
from domain.models import Model as DomainModel
from location.models import Model as LocationModel
from vendor.models import Model as VendorModel
from operatingsystem.models import Model as OperatingsystemModel
from cluster.models import Model as ClusterModel
from clusterpackage.models import Model as ClusterPackageModel
from clustersoftware.models import Model as ClusterSoftwareModel
from clusterpackagetype.models import Model as ClusterPackageTypeModel
from .models import GroupProfile, Invitation, ApiKey


class HistoryAdmin(SimpleHistoryAdmin):
    """Base admin for tenant models that keep simple-history tracks."""

    list_filter = ("group",)


@admin.register(GroupProfile)
class GroupProfileAdmin(admin.ModelAdmin):
    list_display = ("group", "owner", "max_items", "max_users")
    search_fields = ("group__name", "owner__username")
    raw_id_fields = ("group", "owner")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "group", "created_at", "accepted_at", "is_expired")
    search_fields = ("email",)
    readonly_fields = ("token", "created_at", "created_by")
    raw_id_fields = ("group",)


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "client_id",
        "user",
        "is_active",
        "created_at",
        "last_used_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "client_id", "user__username")
    raw_id_fields = ("user",)
    # The secret is one-way hashed; never let it be edited or displayed raw.
    readonly_fields = ("client_id", "secret_hash", "created_at")


@admin.register(PatchtimeModel)
class PatchtimeAdmin(HistoryAdmin):
    list_display = ("name", "group")
    search_fields = ("name",)


@admin.register(ServerModel)
class ServerAdmin(HistoryAdmin):
    list_display = (
        "hostname",
        "status",
        "domain",
        "location",
        "operatingsystem",
        "primary_ip",
        "group",
    )
    list_filter = ("status", "operatingsystem", "cluster", "location", "group")
    search_fields = ("hostname", "primary_ip", "management_hostname")


@admin.register(ServermodelModel)
class ServermodelAdmin(HistoryAdmin):
    list_display = ("name", "vendor", "group")
    list_filter = ("vendor", "group")
    search_fields = ("name",)


@admin.register(StatusModel)
class StatusAdmin(HistoryAdmin):
    list_display = ("name", "group")
    search_fields = ("name",)


@admin.register(DomainModel)
class DomainAdmin(HistoryAdmin):
    list_display = ("name", "group")
    search_fields = ("name",)


@admin.register(LocationModel)
class LocationAdmin(HistoryAdmin):
    list_display = ("name", "country", "group")
    search_fields = ("name", "country")


@admin.register(VendorModel)
class VendorAdmin(HistoryAdmin):
    list_display = ("name", "is_hardware", "is_software", "group")
    list_filter = ("is_hardware", "is_software", "group")
    search_fields = ("name",)


@admin.register(OperatingsystemModel)
class OperatingsystemAdmin(HistoryAdmin):
    list_display = ("version", "vendor", "group")
    list_filter = ("vendor", "group")
    search_fields = ("version",)


@admin.register(ClusterModel)
class ClusterAdmin(HistoryAdmin):
    list_display = ("name", "clustersoftware", "group")
    list_filter = ("clustersoftware", "group")
    search_fields = ("name",)


@admin.register(ClusterPackageModel)
class ClusterPackageAdmin(HistoryAdmin):
    list_display = ("name", "cluster", "package_type", "status", "host", "group")
    list_filter = ("package_type", "status", "cluster", "group")
    search_fields = ("name", "host", "description")


@admin.register(ClusterSoftwareModel)
class ClusterSoftwareAdmin(HistoryAdmin):
    list_display = ("name", "version", "vendor", "group")
    list_filter = ("vendor", "group")
    search_fields = ("name", "version")


@admin.register(ClusterPackageTypeModel)
class ClusterPackageTypeAdmin(HistoryAdmin):
    list_display = ("name", "group")
    search_fields = ("name",)


class GroupProfileInline(admin.StackedInline):
    model = GroupProfile
    can_delete = False


class GroupAdminWithProfile(GroupAdmin):
    inlines = [GroupProfileInline]

    def profile_owner(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.owner if profile and profile.owner else "-"

    profile_owner.short_description = "Owner"

    def profile_max_items(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.max_items if profile else "-"

    profile_max_items.short_description = "Max items"

    def profile_max_users(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.max_users if profile else "-"

    profile_max_users.short_description = "Max users"

    list_display = ("name", "profile_owner", "profile_max_items", "profile_max_users")


class UserAdminWithGroups(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    )


admin.site.unregister(Group)
admin.site.register(Group, GroupAdminWithProfile)

admin.site.unregister(User)
admin.site.register(User, UserAdminWithGroups)
