from django.db import models, migrations
from django.utils.text import slugify
from django.utils.timezone import now

from successstories.utils import get_field_list, convert_to_datetime

MARKER = '.. Migrated from Pages model.\n\n'
DEFAULT_URL = 'https://www.python.org/'

normalized_company_names = {
    'dlink': 'D-Link',
    'astra': 'AstraZeneca',
    'bats': 'BATS',
    'carmanah': 'Carmanah Technologies Inc.',
    'devnet': 'DevNet',
    'esr': 'ESR',
    'ezro': 'devIS',
    'forecastwatch': 'ForecastWatch.com',
    'gravityzoo': 'GravityZoo',
    'gusto': 'Gusto',
    'ilm': 'ILM',
    'loveintros': 'LoveIntros',
    'mayavi': 'MayaVi',
    'mmtk': 'MMTK',
    'natsworld': 'Nat\'s World',
    'projectpipe': 'ProjectPipe',
    'resolver': 'Resolver Systems',
    'siena': 'Siena Technology Ltd.',
    'st-andrews': 'University of St Andrews',
    'tempest': 'TEMPEST',
    'testgo': 'Test&Go',
    'tribon': 'Tribon Solutions',
    'tttech': 'TTTech',
    'usa': 'USA',
    'wingide': 'Wing IDE',
    'wordstream': 'WordStream',
    'xist': 'XIST',
}
fix_category_names = {
    'Software Devleopment': 'Software Development',
    'Science': 'Scientific',
}


def migrate_old_content(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    Story = apps.get_model('successstories', 'Story')
    StoryCategory = apps.get_model('successstories', 'StoryCategory')
    db_alias = schema_editor.connection.alias
    pages = Page.objects.using(db_alias).filter(
        path__startswith='about/success/',
        content_markup_type='restructuredtext'
    )
    stories = []
    for page in pages.iterator():
        field_list = dict(get_field_list(page.content.raw))
        extract_company_name = page.path.split('/')[-1]
        company_name = normalized_company_names.get(
            extract_company_name.lower(), extract_company_name.title()
        )
        company_slug = slugify(company_name)
        check_story = Story.objects.filter(slug=company_slug).exists()
        if check_story:
            # Move to the next one if story is already in the table.
            continue
        company_url = field_list.get('website',
                                     field_list.get('web site', DEFAULT_URL))
        category_cleaned = field_list['category'].strip().split(',')[0].strip()
        category_cleaned = fix_category_names.get(category_cleaned,
                                                  category_cleaned)
        category, _ = StoryCategory.objects.get_or_create(
            name=category_cleaned,
            defaults={
                'slug': slugify(category_cleaned),
            }
        )
        story = Story(
            name=field_list['title'],
            slug=company_slug,
            created=convert_to_datetime(field_list['date']),
            company_name=company_name,
            company_url=company_url,
            category=category,
            author=field_list['author'],
            pull_quote=field_list['summary'],
            content=MARKER + page.content.raw,
            is_published=True,
            updated=now(),
        )
        stories.append(story)
    Story.objects.bulk_create(stories)


def delete_migrated_content(apps, schema_editor):
    Story = apps.get_model('successstories', 'Story')
    db_alias = schema_editor.connection.alias
    Story.objects.using(db_alias).filter(content__startswith=MARKER).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('successstories', '0005_auto_20170726_0645'),
        # Added dependency to enable using models from pages
        # in migrate_old_content.
        ('pages', '0002_auto_20150416_1853'),
    ]

    operations = [
        migrations.RunPython(migrate_old_content, delete_migrated_content),
    ]
