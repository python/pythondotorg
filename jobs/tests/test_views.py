from django.core.urlresolvers import reverse
from django.test import TestCase

from companies.models import Company

from .. import admin     # coverage FTW
from ..models import Job, JobCategory, JobType


class JobsViewTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name='Kulfun Games',
            slug='kulfun-games',
        )

        self.job_category = JobCategory.objects.create(
            name='Game Production',
            slug='game-production'
        )

        self.job_type = JobType.objects.create(
            name='FrontEnd Developer',
            slug='frontend-developer'
        )

        self.job = Job.objects.create(
            company=self.company,
            description='Lorem ipsum dolor sit amet',
            category=self.job_category,
            city='Memphis',
            region='TN',
            country='USA',
            email='hr@company.com'
        )
        self.job.job_types.add(self.job_type)

    def test_job_list(self):
        url = reverse('jobs:job_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse('jobs:job_list_type', kwargs={'slug': self.job_type.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        url = reverse('jobs:job_list_category', kwargs={'slug': self.job_category.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.status_code, 200)

        url = reverse('jobs:job_list_location', kwargs={'slug': self.job.location_slug})
        response = self.client.get(url)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.status_code, 200)

        url = reverse('jobs:job_list_company', kwargs={'slug': self.company.slug})
        response = self.client.get(url)
        self.assertEqual(len(response.context['object_list']), 1)

        self.assertEqual(response.status_code, 200)

    def test_job_detail(self):
        url = self.job.get_absolute_url()
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_job_create(self):
        url = reverse('jobs:job_create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        company = Company.objects.create(
            name='StudioNow',
            slug='studionow',
        )

        post_data = {
            'category': self.job_category.pk,
            'job_types': [self.job_type.pk],
            'company': company.pk,
            'city': 'San Diego',
            'region': 'CA',
            'country': 'USA',
            'description': 'Lorem ipsum dolor sit amet',
            'email': 'hr@company.com'
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        jobs = Job.objects.filter(company__slug='studionow')
        self.assertEqual(len(jobs), 1)

        job = jobs[0]
        self.assertNotEqual(job.created, None)
        self.assertNotEqual(job.updated, None)
        self.assertEqual(job.creator, None)
