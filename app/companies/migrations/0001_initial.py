from django.db import models, migrations
import markupfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('about', markupfield.fields.MarkupField(rendered_field=True, blank=True)),
                ('about_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='restructuredtext', blank=True)),
                ('contact', models.CharField(max_length=100, blank=True, null=True)),
                ('_about_rendered', models.TextField(editable=False)),
                ('email', models.EmailField(max_length=75, blank=True, null=True)),
                ('url', models.URLField(verbose_name='URL', blank=True, null=True)),
                ('logo', models.ImageField(upload_to='companies/logos/', blank=True, null=True)),
            ],
            options={
                'verbose_name': 'company',
                'verbose_name_plural': 'companies',
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
    ]
