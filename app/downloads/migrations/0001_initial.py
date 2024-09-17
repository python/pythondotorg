from django.db import models, migrations
import markupfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OS',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='downloads_os_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='downloads_os_modified', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Operating System',
                'verbose_name_plural': 'Operating Systems',
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('version', models.IntegerField(choices=[(3, 'Python 3.x.x'), (2, 'Python 2.x.x'), (1, 'Python 1.x.x')], default=2)),
                ('is_latest', models.BooleanField(help_text="Set this if this should be considered the latest release for the major version. Previous 'latest' versions will automatically have this flag turned off.", db_index=True, verbose_name='Is this the latest release?', default=False)),
                ('is_published', models.BooleanField(help_text='Whether or not this should be considered a released/published version', db_index=True, verbose_name='Is Published?', default=False)),
                ('pre_release', models.BooleanField(help_text='Boolean to denote pre-release/beta/RC versions', db_index=True, verbose_name='Pre-release', default=False)),
                ('show_on_download_page', models.BooleanField(help_text='Whether or not to show this release on the main /downloads/ page', db_index=True, default=True)),
                ('release_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('release_notes_url', models.URLField(verbose_name='Release Notes URL', blank=True)),
                ('content', markupfield.fields.MarkupField(default='', rendered_field=True)),
                ('content_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='restructuredtext')),
                ('_content_rendered', models.TextField(editable=False)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='downloads_release_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='downloads_release_modified', blank=True, on_delete=models.CASCADE)),
                ('release_page', models.ForeignKey(null=True, to='pages.Page', related_name='release', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Release',
                'verbose_name_plural': 'Releases',
                'ordering': ('name',),
                'get_latest_by': 'release_date',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReleaseFile',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_source', models.BooleanField(verbose_name='Is Source Distribution', default=False)),
                ('url', models.URLField(help_text='Download URL', verbose_name='URL', unique=True, db_index=True)),
                ('gpg_signature_file', models.URLField(help_text='GPG Signature URL', verbose_name='GPG SIG URL', blank=True)),
                ('md5_sum', models.CharField(max_length=200, verbose_name='MD5 Sum', blank=True)),
                ('filesize', models.IntegerField(default=0)),
                ('download_button', models.BooleanField(help_text='Use for the supernav download button for this OS', default=False)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='downloads_releasefile_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='downloads_releasefile_modified', blank=True, on_delete=models.CASCADE)),
                ('os', models.ForeignKey(verbose_name='OS', to='downloads.OS', related_name='releases', on_delete=models.CASCADE)),
                ('release', models.ForeignKey(to='downloads.Release', related_name='files', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Release File',
                'verbose_name_plural': 'Release Files',
                'ordering': ('-release__is_published', 'release__name', 'os__name', 'name'),
            },
            bases=(models.Model,),
        ),
    ]
