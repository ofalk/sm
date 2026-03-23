# Multi-tenancy Developer Guide

This project uses a group-based multi-tenancy system. Every primary entity is partitioned by a Django `Group`.

## How to make a Model Multi-tenant

### 1. Update the Model

Add a `group` ForeignKey and update the `UniqueConstraint` in `Meta`:

```python
from django.db import models
from django.contrib.auth.models import Group


class Model(models.Model):
    name = models.CharField(max_length=255)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "group"], name="unique_name_per_group"
            )
        ]
```

### 2. Update the View

Use the `MultiTenantMixin` from `sm.mixins`. It handles:

- Filtering the QuerySet based on the user's groups.
- Auto-assigning the user's primary group on creation.
- Enforcing item quotas (max items per group).

```python
from sm.mixins import MultiTenantMixin
from django.views.generic import ListView, CreateView


class MyListView(MultiTenantMixin, ListView):
    model = MyModel


class MyCreateView(MultiTenantMixin, CreateView):
    model = MyModel
    # MultiTenantMixin ensures quota is checked before save()
```

### 3. Update the API (DRF)

Use `APIMultiTenantMixin` for ViewSets:

```python
from sm.mixins import APIMultiTenantMixin
from rest_framework import viewsets


class MyViewSet(APIMultiTenantMixin, viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
```

## Quota Management

Quotas are stored in the `GroupProfile` model.

- `max_items`: Sum of all Servers, Clusters, Domains, Vendors, and OS.
- `max_users`: Maximum members allowed in the group.

## Permissions

- **Superusers**: Can see and edit everything across all groups.
- **Staff**: Can manage all groups and quotas via `/admin/users/`.
- **Group Owners**: Can manage their own group members and toggle "Edit" permissions for their group via the "Group Members" menu.
- **Users**: Can only see items belonging to their groups.
