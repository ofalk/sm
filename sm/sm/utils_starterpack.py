from pathlib import Path
import yaml
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import transaction
from vendor.models import Model as Vendor
from operatingsystem.models import Model as OS
from typing import Dict, List, Any


def _load_fixture(app_label: str) -> List[Any]:
    """Loads a YAML fixture from an app's fixtures dir; [] if absent."""
    path = Path(settings.BASE_DIR) / app_label / "fixtures" / "01_initial.yaml"
    if not path.is_file():
        return []
    with open(path) as f:
        return yaml.safe_load(f) or []


def import_starter_pack(group: Group) -> Dict[str, int]:
    """
    Imports vendors and operating systems from fixtures into the specified
    group. Runs atomically so a partial import can never leave the group in a
    half-populated state.
    """
    # Vendor name (as referenced from the OS fixture) -> group-scoped Vendor
    vendor_map = {}
    vendor_count = 0
    os_count = 0

    with transaction.atomic():
        vendor_data = _load_fixture("vendor")
        for item in vendor_data:
            if not isinstance(item, dict) or item.get("model") != "vendor.model":
                continue
            fields = item["fields"]
            vendor, created = Vendor.objects.get_or_create(
                name=fields["name"],
                group=group,
                defaults={
                    "is_hardware": fields.get("is_hardware", True),
                    "is_software": fields.get("is_software", True),
                },
            )
            vendor_map[fields["name"]] = vendor
            if created:
                vendor_count += 1

        os_data = _load_fixture("operatingsystem")
        for item in os_data:
            if (
                not isinstance(item, dict)
                or item.get("model") != "operatingsystem.model"
            ):
                continue
            fields = item["fields"]
            vendor_names = fields.get("vendor")
            if isinstance(vendor_names, list):
                vendor_name = vendor_names[0] if vendor_names else None
            else:
                vendor_name = vendor_names

            vendor = vendor_map.get(vendor_name) if vendor_name else None
            if vendor is None:
                continue
            _, created = OS.objects.get_or_create(
                version=fields["version"], vendor=vendor, group=group
            )
            if created:
                os_count += 1

    return {"vendors": vendor_count, "os": os_count}
