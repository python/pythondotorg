from django.db import models, migrations
import markupfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('company_name', models.CharField(max_length=100, blank=True, null=True)),
                ('company_description', markupfield.fields.MarkupField(rendered_field=True, blank=True)),
                ('job_title', models.CharField(max_length=100)),
                ('company_description_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='restructuredtext', blank=True)),
                ('_company_description_rendered', models.TextField(editable=False)),
                ('city', models.CharField(max_length=100)),
                ('region', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100, db_index=True)),
                ('location_slug', models.SlugField(max_length=350, editable=False)),
                ('country_slug', models.SlugField(max_length=100, editable=False)),
                ('description', markupfield.fields.MarkupField(rendered_field=True, blank=True)),
                ('description_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='restructuredtext', blank=True)),
                ('requirements', markupfield.fields.MarkupField(rendered_field=True, blank=True)),
                ('contact', models.CharField(max_length=100, blank=True, null=True)),
                ('_description_rendered', models.TextField(editable=False)),
                ('requirements_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='restructuredtext', blank=True)),
                ('_requirements_rendered', models.TextField(editable=False)),
                ('email', models.EmailField(max_length=75)),
                ('url', models.URLField(verbose_name='URL', blank=True, null=True)),
                ('status', models.CharField(max_length=20, choices=[('draft', 'draft'), ('review', 'review'), ('approved', 'approved'), ('rejected', 'rejected'), ('archived', 'archived'), ('removed', 'removed'), ('expired', 'expired')], default='review', db_index=True)),
                ('dt_start', models.DateTimeField(null=True, verbose_name='Job start date', blank=True)),
                ('dt_end', models.DateTimeField(null=True, verbose_name='Job end date', blank=True)),
                ('telecommuting', models.BooleanField(default=False)),
                ('agencies', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(db_index=True, default=False)),
            ],
            options={
                'verbose_name': 'job',
                'permissions': [('can_moderate_jobs', 'Can moderate Job listings')],
                'verbose_name_plural': 'jobs',
                'ordering': ('-created',),
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='JobCategory',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'verbose_name': 'job category',
                'verbose_name_plural': 'job categories',
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='JobType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'verbose_name': 'job technologies',
                'verbose_name_plural': 'job technologies',
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='job',
            name='category',
            field=models.ForeignKey(to='jobs.JobCategory', related_name='jobs', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='company',
            field=models.ForeignKey(help_text='Choose a specific company here or enter Name and Description Below', null=True, to='companies.Company', related_name='jobs', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='creator',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='jobs_job_creator', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='job_types',
            field=models.ManyToManyField(to='jobs.JobType', verbose_name='Job technologies', related_name='jobs', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='last_modified_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='jobs_job_modified', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
