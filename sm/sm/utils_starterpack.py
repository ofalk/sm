import yaml
import os
from django.conf import settings
from django.contrib.auth.models import Group
from vendor.models import Model as Vendor
from operatingsystem.models import Model as OS
from typing import Dict, List, Any, Optional, Union


def import_starter_pack(group: Group) -> Dict[str, int]:
    """
    Imports vendors and operating systems from fixtures into the specified group.
    """
    vendor_count = 0
    os_count = 0

    # 1. Import Vendors
    vendor_fixture_path = os.path.join(
        settings.BASE_DIR, "vendor", "fixtures", "01_initial.yaml"
    )
    with open(vendor_fixture_path) as f:
        vendor_data = yaml.safe_load(f)

    vendor_map = {}  # To keep track of created vendors for OS lookup

    for item in vendor_data:
        if item["model"] == "vendor.model":
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

    # 2. Import Operating Systems
    os_fixture_path = os.path.join(
        settings.BASE_DIR, "operatingsystem", "fixtures", "01_initial.yaml"
    )
    with open(os_fixture_path) as f:
        os_data = yaml.safe_load(f)

    for item in os_data:
        if item["model"] == "operatingsystem.model":
            fields = item["fields"]
            vendor_names = fields["vendor"]
            if isinstance(vendor_names, list):
                vendor_name = vendor_names[0]
            else:
                vendor_name = vendor_names

            vendor = vendor_map.get(vendor_name)
            if vendor:
                os_obj, created = OS.objects.get_or_create(
                    version=fields["version"], vendor=vendor, group=group
                )
                if created:
                    os_count += 1

    return {"vendors": vendor_count, "os": os_count}
