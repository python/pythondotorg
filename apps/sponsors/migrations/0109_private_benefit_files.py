from django.db import migrations, models

import apps.sponsors.models.assets
import apps.sponsors.models.benefits
import apps.sponsors.storage


class Migration(migrations.Migration):
    dependencies = [
        ("sponsors", "0108_contract_document_max_length"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fileasset",
            name="file",
            field=models.FileField(
                null=True,
                storage=apps.sponsors.storage.get_asset_storage,
                upload_to=apps.sponsors.models.assets.generic_asset_path,
            ),
        ),
        migrations.AlterField(
            model_name="providedfileasset",
            name="shared_file",
            field=models.FileField(
                blank=True,
                null=True,
                storage=apps.sponsors.storage.get_asset_storage,
                upload_to=apps.sponsors.models.benefits.provided_file_path,
            ),
        ),
        migrations.AlterField(
            model_name="providedfileassetconfiguration",
            name="shared_file",
            field=models.FileField(
                blank=True,
                null=True,
                storage=apps.sponsors.storage.get_asset_storage,
                upload_to=apps.sponsors.models.benefits.provided_file_path,
            ),
        ),
    ]
