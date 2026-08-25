# Multi-tenancy Developer Guide

This guide provides comprehensive documentation for extending the multi-tenancy system to new apps and models.

## Table of Contents

1. [Overview](#overview)
2. [Core Components](#core-components)
3. [Extending Multi-tenancy to New Models](#extending-multi-tenancy-to-new-models)
4. [Adding Multi-tenancy to Views](#adding-multi-tenancy-to-views)
5. [API Integration](#api-integration)
6. [Quota Management](#quota-management)
7. [Permissions and Security](#permissions-and-security)
8. [Testing Multi-tenancy](#testing-multi-tenancy)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Overview

The multi-tenancy system allows multiple groups (tenants) to use the same application instance while keeping their data isolated. Each tenant has:

- Their own data partition
- Configurable quotas
- Delegated administration capabilities
- Custom permissions

## Core Components

### 1. Data Partitioning

The foundation of multi-tenancy is the `group` field added to all tenant-specific models:

```python
from django.contrib.auth.models import Group


class MyModel(models.Model):
    # ... other fields ...
    group = models.ForeignKey(
        Group,
        editable=False,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="mymodels",  # Use plural name for consistency
    )
```

### 2. Unique Constraints

To allow the same names across different tenants, add group-based unique constraints:

```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=["name", "group"], name="unique_app_mymodel_name_group"
        )
    ]
```

**Global reference data:** PostgreSQL treats NULLs as distinct, so the constraint
above cannot deduplicate global (`group=None`) rows. If your model holds shared
reference data (seeded globally, visible to every tenant), also add a partial
constraint so superusers cannot create duplicate globals — duplicates would
break `get_by_natural_key()` fixture loading:

```python
models.UniqueConstraint(
    fields=["name"],
    condition=Q(group__isnull=True),
    name="unique_app_mymodel_global_name",
)
```

See `servermodel` and `clustersoftware` for working examples.

### 3. Mixins

Two main mixins handle filtering and quota enforcement:

- `MultiTenantMixin`: For Django views
- `APIMultiTenantMixin`: For DRF ViewSets

## Extending Multi-tenancy to New Models

### Step 1: Add the Group Field

Add the `group` ForeignKey to your model as shown above.

### Step 2: Add Unique Constraints

Add group-based unique constraints to the model's Meta class.

### Step 3: Update Views

For Django views, inherit from `MultiTenantMixin`:

```python
from sm.mixins import MultiTenantMixin


class MyModelCreateView(MultiTenantMixin, CreateView):
    model = MyModel
    fields = ["name", "description"]
    success_url = reverse_lazy("mymodel:list")
```

### Step 4: Update API Views

For DRF ViewSets, inherit from `APIMultiTenantMixin`:

```python
from sm.mixins import APIMultiTenantMixin


class MyModelViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
```

### Step 5: Update Quota Management

Add your model to the quota counting logic in `sm/mixins.py`:

```python
# In the check_quota method, add:
from myapp.models import Model as MyModel

count = (
    # ... existing counts ...
    +MyModel.objects.filter(group=group).count()
)
```

### Step 6: Update Permissions

Add your model to the automatic permission sync in `sm/utils_permissions.py`:

```python
app_models = [
    # ... existing models ...
    ("myapp", "model"),
]
```

## Adding Multi-tenancy to Views

### List Views

```python
class MyModelListView(MultiTenantMixin, ListView):
    model = MyModel
    template_name = "myapp/mymodel_list.html"
```

The mixin automatically filters the queryset to show only items belonging to the user's groups or global items (group=None).

### Create Views

```python
class MyModelCreateView(MultiTenantMixin, CreateView):
    model = MyModel
    fields = ["name", "description"]
    success_url = reverse_lazy("mymodel:list")
```

The mixin automatically:

1. Assigns the user's primary group to new items
2. Checks quota limits before saving
3. Shows appropriate error messages if quota is exceeded

### Update and Delete Views

```python
class MyModelUpdateView(MultiTenantMixin, UpdateView):
    model = MyModel
    fields = ["name", "description"]
    success_url = reverse_lazy("mymodel:list")


class MyModelDeleteView(MultiTenantMixin, DeleteView):
    model = MyModel
    success_url = reverse_lazy("mymodel:list")
```

These views inherit the filtering behavior to ensure users can only edit/delete items they have access to.

## API Integration

### ViewSets

```python
from sm.mixins import APIMultiTenantMixin


class MyModelViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    permission_classes = [permissions.DjangoModelPermissions]
```

### Serializers

No changes needed to serializers. The mixin handles group assignment automatically.

### Custom API Endpoints

For custom API views, use the mixin's methods:

```python
from sm.mixins import APIMultiTenantMixin
from rest_framework.views import APIView
from rest_framework.response import Response


class MyCustomAPIView(APIMultiTenantMixin, APIView):
    def get(self, request):
        # Get filtered queryset
        queryset = self.get_queryset()
        # ... your logic ...
        return Response(data)
```

## Quota Management

### Understanding Quotas

Quotas are managed through the `GroupProfile` model:

- `max_items`: Maximum number of items across all models
- `max_users`: Maximum number of users in the group

### Checking Quotas Programmatically

```python
from sm.mixins import MultiTenantMixin

mixin = MultiTenantMixin()
mixin.request = request  # Set the request object

if mixin.check_quota(user_group):
    # Quota available, proceed with creation
    pass
else:
    # Quota exceeded, show error
    pass
```

### Custom Quota Logic

To implement custom quota logic for specific models:

```python
def check_custom_quota(group, model_class):
    """Check quota for a specific model type."""
    if not group or not hasattr(group, "profile"):
        return True

    profile = group.profile
    count = model_class.objects.filter(group=group).count()

    # Implement your custom quota logic here
    return count < profile.max_items
```

## Permissions and Security

### Automatic Permissions

The system automatically grants `view_*` permissions to new groups for all core models.

### Custom Permissions

To add custom permissions to a group:

```python
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# Get the content type for your model
content_type = ContentType.objects.get(app_label="myapp", model="model")

# Get specific permissions
add_permission = Permission.objects.get(content_type=content_type, codename="add_model")

# Add permission to group
group.permissions.add(add_permission)
```

### Permission Management Views

The system provides views for group owners to manage permissions:

- `GroupPermissionEditView`: Allows toggling permissions for different apps

### Security Considerations

1. **Superusers**: Bypass all multi-tenancy filters
2. **Global Items**: Items with `group=None` are visible to all users
3. **Data Isolation**: Always use the mixin's `get_queryset()` method
4. **Direct Queries**: Avoid direct model queries that bypass filtering

## Testing Multi-tenancy

### Test Structure

```python
from django.test import TestCase
from django.contrib.auth.models import User, Group
from myapp.models import MyModel


class MyMultiTenancyTest(TestCase):
    def setUp(self):
        # Create groups
        self.group_a = Group.objects.create(name="Group A")
        self.group_b = Group.objects.create(name="Group B")

        # Create users
        self.user_a = User.objects.create_user(username="user_a", password="test")
        self.user_b = User.objects.create_user(username="user_b", password="test")

        # Assign users to groups
        self.user_a.groups.add(self.group_a)
        self.user_b.groups.add(self.group_b)

        # Create test data
        MyModel.objects.create(name="Item A", group=self.group_a)
        MyModel.objects.create(name="Item B", group=self.group_b)

    def test_data_isolation(self):
        """Test that users only see their group's data."""
        self.client.login(username="user_a", password="test")
        response = self.client.get("/myapp/")

        self.assertContains(response, "Item A")
        self.assertNotContains(response, "Item B")

    def test_quota_enforcement(self):
        """Test that quotas are properly enforced."""
        # Set low quota
        profile = self.group_a.profile
        profile.max_items = 1
        profile.save()

        # Try to create second item (should fail)
        response = self.client.post(
            "/myapp/create/",
            {
                "name": "Item C",
                # ... other fields ...
            },
        )

        self.assertContains(response, "Quota exceeded")
        self.assertEqual(MyModel.objects.filter(group=self.group_a).count(), 1)
```

### Test Coverage

Ensure your tests cover:

1. **Data Isolation**: Users can only see their group's data
2. **Quota Enforcement**: Quotas are properly checked and enforced
3. **Permission Management**: Group owners can manage permissions
4. **Global Items**: Items with no group are visible to all
5. **Superuser Access**: Superusers can see and edit all data
6. **API Endpoints**: All API endpoints respect multi-tenancy

### Running the Suite

- Unit/API tests: `manage.py test --exclude-tag=browser` (auto-discovers all test modules).
- Browser tests: `manage.py test --tag=browser` (Playwright, Chromium + Firefox).
- CI runs against PostgreSQL with `DEBUG=False`; `SmTestRunner` (`sm/sm/runner.py`) clears stray sessions before the test database is dropped, and settings disable persistent connections (`CONN_MAX_AGE=0`) during tests. Keep both in place when adding live-server tests.

## Best Practices

### Model Design

1. **Always add the group field** to tenant-specific models
2. **Use consistent related_names** (plural form of model name)
3. **Add unique constraints** for fields that should be unique per tenant
4. **Consider null=True, blank=True** for the group field to allow global items

### View Design

1. **Always inherit from the mixins** for tenant-specific views
2. **Use get_queryset()** instead of direct model queries
3. **Handle quota errors gracefully** with user-friendly messages
4. **Test superuser behavior** separately

### Performance

1. **Index the group field** for better query performance
2. **Use select_related/prefetch_related** for related group data
3. **Cache group memberships** for frequently accessed data
4. **Consider denormalization** for complex multi-tenant queries

### Security

1. **Never bypass the mixin's filtering** in custom queries
2. **Validate all inputs** even with mixin protection
3. **Use Django's permission system** for fine-grained control
4. **Audit sensitive operations** related to group management

## Troubleshooting

### Common Issues

1. **"Group object has no attribute 'profile'"**
   - Ensure the GroupProfile is created automatically via the post_save signal
   - Check that the signal is properly connected

2. **Data visible to wrong users**
   - Verify all views inherit from the appropriate mixin
   - Check for direct model queries that bypass filtering
   - Ensure superusers are handled correctly

3. **Quota not enforced**
   - Verify the model is included in quota counting
   - Check that the mixin's form_valid method is called
   - Ensure transactions are working properly

4. **Performance issues**
   - Add database indexes for the group field
   - Optimize complex queries with select_related
   - Consider caching for frequently accessed data

### Debugging Tips

1. **Check group assignments**:

   ```python
   user.groups.all()  # Check user's groups
   model.group  # Check model's group assignment
   ```

2. **Inspect filtered querysets**:

   ```python
   queryset = MyModel.objects.all()
   filtered = queryset.filter(Q(group__in=user.groups.all()) | Q(group__isnull=True))
   print(filtered.query)  # See the generated SQL
   ```

3. **Test permissions**:
   ```python
   user.has_perm("myapp.view_mymodel")  # Check specific permission
   user.get_all_permissions()  # See all permissions
   ```

## Migration Guide

### Adding Multi-tenancy to Existing Models

1. **Add the group field** with null=True
2. **Create and run migrations**
3. **Update existing data** to assign groups as needed
4. **Add unique constraints** in a separate migration
5. **Update views** to use the mixins
6. **Test thoroughly** before deploying

### Backward Compatibility

- Existing data with `group=None` becomes global (visible to all)
- Gradually migrate global data to specific groups as needed
- Consider adding a migration to set default groups for existing data

## Advanced Topics

### Cross-Tenant Features

For features that need to work across tenants:

```python
# Temporarily disable filtering for admin reports
def get_cross_tenant_data():
    if request.user.is_superuser:
        return MyModel.objects.all()  # All data for superusers
    else:
        return MyModel.objects.filter(
            group__in=request.user.groups.all()
        )  # Filtered for others
```

### Custom Group Logic

```python
# Custom group assignment logic
def get_user_primary_group(user):
    """Get user's primary group with custom logic."""
    # Your custom logic here
    return user.groups.first()
```

### Soft Deletion

Consider implementing soft deletion for multi-tenant data:

```python
class MyModel(models.Model):
    # ... other fields ...
    group = models.ForeignKey(Group, ...)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active_objects = ActiveManager()  # Custom manager excluding deleted items


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
```

## Conclusion

This guide provides a comprehensive overview of extending the multi-tenancy system. Always test thoroughly when adding new features and consider the security implications of any changes.

For questions or issues, refer to the main documentation or contact the development team.
