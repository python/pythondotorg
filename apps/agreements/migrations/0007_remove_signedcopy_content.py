from django.db import migrations, models

import apps.agreements.models.agreements
import apps.agreements.storage


class Migration(migrations.Migration):
    dependencies = [("agreements", "0006_move_signed_copies_to_storage")]

    operations = [
        migrations.RemoveField(model_name="signedcopy", name="content"),
        migrations.AlterField(
            model_name="signedcopy",
            name="file",
            field=models.FileField(
                storage=apps.agreements.storage.get_agreement_storage,
                upload_to=apps.agreements.models.agreements.signed_copy_path,
            ),
        ),
    ]
