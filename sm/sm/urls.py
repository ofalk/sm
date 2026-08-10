from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .views import (
    DashboardView,
    SearchView,
    ImportStarterPackView,
    HistoryDiffView,
    TermsView,
    PrivacyView,
    ImpressumView,
    HealthView,
)
from .views_admin import UserListView, GroupProfileUpdateView
from .views_group import (
    GroupMemberListView,
    AddGroupMemberView,
    RemoveGroupMemberView,
    GroupPermissionUpdateView,
    UserPermissionUpdateView,
    InviteGroupMemberView,
    AcceptInvitationView,
    GroupFilterView,
    GroupCreateView,
)
from .views_avatars import avatar_proxy
from .views_api_keys import ApiKeyListView, RevokeApiKeyView
from .api.views import (
    ServerViewSet,
    VendorViewSet,
    StatusViewSet,
    LocationViewSet,
    DomainViewSet,
    PatchtimeViewSet,
    OSViewSet,
    ServerModelViewSet,
    ClusterViewSet,
    ClusterPackageViewSet,
    ClusterSoftwareViewSet,
    ClusterPackageTypeViewSet,
)
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"servers", ServerViewSet, basename="api-server")
router.register(r"vendors", VendorViewSet, basename="api-vendor")
router.register(r"statuses", StatusViewSet, basename="api-status")
router.register(r"locations", LocationViewSet, basename="api-location")
router.register(r"domains", DomainViewSet, basename="api-domain")
router.register(r"patchtimes", PatchtimeViewSet, basename="api-patchtime")
router.register(r"operatingsystems", OSViewSet, basename="api-operatingsystem")
router.register(r"servermodels", ServerModelViewSet, basename="api-servermodel")
router.register(r"clusters", ClusterViewSet, basename="api-cluster")
router.register(
    r"clusterpackages", ClusterPackageViewSet, basename="api-clusterpackage"
)
router.register(
    r"clustersoftware", ClusterSoftwareViewSet, basename="api-clustersoftware"
)
router.register(
    r"clusterpackagetypes",
    ClusterPackageTypeViewSet,
    basename="api-clusterpackagetype",
)

urlpatterns = [
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    # API
    path("api/", include(router.urls)),
    # API Schema & Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # API Key Management
    path("account/api-keys/", ApiKeyListView.as_view(), name="api_keys"),
    path(
        "account/api-keys/revoke/<int:pk>/",
        RevokeApiKeyView.as_view(),
        name="api_key_revoke",
    ),
    # Allauth URLs
    path("accounts/", include("allauth.urls")),
    # Dashboard & Search
    path("", DashboardView.as_view(), name="dashboard"),
    path("search/", SearchView.as_view(), name="search"),
    path(
        "starter-pack/import/",
        ImportStarterPackView.as_view(),
        name="starter_pack_import",
    ),
    path("avatar/<str:email_hash>/", avatar_proxy, name="avatar_proxy"),
    path(
        "history/<str:app_label>/<str:model_name>/<int:history_id>/",
        HistoryDiffView.as_view(),
        name="history_diff",
    ),
    # Legal Pages
    path("terms/", TermsView.as_view(), name="terms"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("impressum/", ImpressumView.as_view(), name="impressum"),
    path("health/", HealthView.as_view(), name="health"),
    # User Management (Staff)
    path("admin/users/", UserListView.as_view(), name="user_management_list"),
    path(
        "admin/groups/<int:pk>/",
        GroupProfileUpdateView.as_view(),
        name="group_profile_edit",
    ),
    # Group Management (Owner)
    path("group/members/", GroupMemberListView.as_view(), name="group_member_list"),
    path("group/create/", GroupCreateView.as_view(), name="group_create"),
    path(
        "group/members/add/<int:group_id>/",
        AddGroupMemberView.as_view(),
        name="group_member_add",
    ),
    path(
        "group/members/remove/<int:group_id>/<int:user_id>/",
        RemoveGroupMemberView.as_view(),
        name="group_member_remove",
    ),
    path(
        "group/permissions/<int:group_id>/",
        GroupPermissionUpdateView.as_view(),
        name="group_permission_edit",
    ),
    path(
        "group/permissions/<int:group_id>/user/<int:user_id>/",
        UserPermissionUpdateView.as_view(),
        name="group_user_permission_edit",
    ),
    path(
        "group/invite/<int:group_id>/",
        InviteGroupMemberView.as_view(),
        name="group_member_invite",
    ),
    path(
        "invitation/<uuid:token>/",
        AcceptInvitationView.as_view(),
        name="accept_invitation",
    ),
    path(
        "group/filter/",
        GroupFilterView.as_view(),
        name="group_filter",
    ),
    # Project Apps
    path("cluster/", include("cluster.urls")),
    path("operatingsystem/", include("operatingsystem.urls")),
    path("clusterpackage/", include("clusterpackage.urls")),
    path("patchtime/", include("patchtime.urls")),
    path("location/", include("location.urls")),
    path("servermodel/", include("servermodel.urls")),
    path("server/", include("server.urls")),
    path("status/", include("status.urls")),
    path("domain/", include("domain.urls")),
    path("clustersoftware/", include("clustersoftware.urls")),
    path("clusterpackagetype/", include("clusterpackagetype.urls")),
    path("vendor/", include("vendor.urls")),
]

if "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
