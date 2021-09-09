from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0014_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='email',
            field=models.EmailField(max_length=254, verbose_name='Contact email'),
        ),
    ]
