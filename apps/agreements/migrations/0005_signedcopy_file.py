from django.db import migrations, models

import apps.agreements.models.agreements
import apps.agreements.storage


class Migration(migrations.Migration):
    dependencies = [("agreements", "0004_orderline_services")]

    operations = [
        migrations.AddField(
            model_name="signedcopy",
            name="file",
            field=models.FileField(
                null=True,
                storage=apps.agreements.storage.get_agreement_storage,
                upload_to=apps.agreements.models.agreements.signed_copy_path,
            ),
        ),
        # Nullable so that reversing 0007 can re-add the column before 0006 restores the bytes.
        migrations.AlterField(
            model_name="signedcopy",
            name="content",
            field=models.BinaryField(null=True),
        ),
    ]
