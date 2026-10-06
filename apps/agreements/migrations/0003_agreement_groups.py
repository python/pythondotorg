from django.db import migrations


def create_agreement_groups(apps, schema_editor):
    groups = apps.get_model("auth", "Group").objects.using(schema_editor.connection.alias)
    for name in ("Agreements Editors", "Agreements Administrators"):
        groups.get_or_create(name=name)
    apps.get_model("auth", "Permission").objects.using(schema_editor.connection.alias).filter(
        content_type__app_label="agreements", content_type__model="agreement", codename="manage_agreement"
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("agreements", "0002_configurable_programs"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.AlterModelOptions(name="agreement", options={"ordering": ("-offered_at",)}),
        migrations.RunPython(create_agreement_groups, migrations.RunPython.noop),
    ]
