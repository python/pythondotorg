from django.db import models, migrations
import markupfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('jobs', '0010_auto_20150416_1853'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobReviewComment',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created', models.DateTimeField(blank=True, default=django.utils.timezone.now, db_index=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('comment', markupfield.fields.MarkupField(rendered_field=True)),
                ('comment_markup_type', models.CharField(choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')], max_length=30, default='restructuredtext')),
                ('_comment_rendered', models.TextField(editable=False)),
                ('creator', models.ForeignKey(related_name='jobs_jobreviewcomment_creator', to=settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)),
                ('job', models.ForeignKey(related_name='review_comments', to='jobs.Job', on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(related_name='jobs_jobreviewcomment_modified', to=settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
