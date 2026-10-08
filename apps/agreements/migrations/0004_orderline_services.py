from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations, models

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def preserve_included_services(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    lines = apps.get_model("agreements", "OrderLine").objects.using(schema_editor.connection.alias)
    for line in lines.select_related("order__program").iterator():
        definition = line.order.catalog_snapshot or line.order.program.definition
        agreement = next((item for item in definition["agreements"] if item["slug"] == line.agreement), None)
        if agreement is None:
            continue
        services = [
            service["key"]
            for service in agreement.get("services", [])
            if not service.get("tiers") or line.tier in service["tiers"]
        ]
        lines.filter(pk=line.pk).update(services=services)


class Migration(migrations.Migration):
    dependencies = [("agreements", "0003_agreement_groups")]

    operations = [
        migrations.AddField(
            model_name="orderline",
            name="services",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(preserve_included_services, migrations.RunPython.noop),
    ]
