from django.db import models, migrations
from django.conf import settings
import django.core.validators
import markupfield.fields
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(verbose_name='last login', default=django.utils.timezone.now)),
                ('is_superuser', models.BooleanField(help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status', default=False)),
                ('username', models.CharField(help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=30, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username.', 'invalid')], verbose_name='username', unique=True)),
                ('first_name', models.CharField(blank=True, verbose_name='first name', max_length=30)),
                ('last_name', models.CharField(blank=True, verbose_name='last name', max_length=30)),
                ('email', models.EmailField(blank=True, verbose_name='email address', max_length=75)),
                ('is_staff', models.BooleanField(help_text='Designates whether the user can log into this admin site.', verbose_name='staff status', default=False)),
                ('is_active', models.BooleanField(help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active', default=True)),
                ('date_joined', models.DateTimeField(verbose_name='date joined', default=django.utils.timezone.now)),
                ('bio', markupfield.fields.MarkupField(blank=True, rendered_field=True)),
                ('bio_markup_type', models.CharField(choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], max_length=30, default='markdown', blank=True)),
                ('search_visibility', models.IntegerField(choices=[(1, 'Allow search engines to index my profile page (recommended)'), (0, "Don't allow search engines to index my profile page")], default=1)),
                ('_bio_rendered', models.TextField(editable=False)),
                ('email_privacy', models.IntegerField(choices=[(0, 'Anyone can see my e-mail address'), (1, 'Only logged-in users can see my e-mail address'), (2, 'No one can ever see my e-mail address')], verbose_name='E-mail privacy', default=2)),
                ('groups', models.ManyToManyField(help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', related_name='user_set', blank=True, related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(help_text='Specific permissions for this user.', related_name='user_set', blank=True, related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name_plural': 'users',
                'verbose_name': 'user',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('legal_name', models.CharField(max_length=100)),
                ('preferred_name', models.CharField(max_length=100)),
                ('email_address', models.EmailField(max_length=100)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('region', models.CharField(blank=True, verbose_name='State, Province or Region', max_length=100)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('postal_code', models.CharField(blank=True, max_length=20)),
                ('psf_code_of_conduct', models.NullBooleanField(verbose_name='I agree to the PSF Code of Conduct')),
                ('psf_announcements', models.NullBooleanField(verbose_name='I would like to receive occasional PSF email announcements')),
                ('created', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, blank=True, related_name='membership', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
