from django.test import TestCase
from django.core.management import call_command
from django.core.urlresolvers import reverse

from .. import admin # Coverage FTW
from ..models import PepType, PepStatus, PepOwner, PepCategory, Pep

import json


class PEPTests(TestCase):

    def setUp(self):
        call_command('generate_initial_pep_data')

        self.standards_type = PepType.objects.get(abbreviation='S')
        self.informational_type = PepType.objects.get(abbreviation='I')

        self.cat1 = PepCategory.objects.get(name='Meta-PEPs (PEPs baout PEPs or Processes)')
        self.cat2 = PepCategory.objects.get(name='Other Informational PEPs')
        self.cat3 = PepCategory.objects.get(name='Open PEPs (under consideration)')

        self.accepted = PepStatus.objects.get(name='Accepted proposal')
        self.draft = PepStatus.objects.get(name='Draft proposal')

        # Owners
        self.owner1 = PepOwner.objects.create(
            name='Frank Wiles',
            email='frank@revsys.com',
        )
        self.owner2 = PepOwner.objects.create(
            name='Jacob Kaplan-Moss',
            email='jacob@jacobian.org',
        )
        self.owner3 = PepOwner.objects.create(
            name='Jeff Triplett',
            email='jeff@revsys.com',
        )

        self.pep1 = Pep.objects.create(
            type=self.standards_type,
            status=self.accepted,
            category=self.cat1,
            title='Test Pep 1',
            number=1,
            url='http://www.python.org/peps/pep-1/'
        )
        self.pep1.owners.add(self.owner1)

        self.pep2 = Pep.objects.create(
            type=self.informational_type,
            status=self.draft,
            category=self.cat2,
            title='Test Pep 1',
            number=1,
            url='http://www.python.org/peps/pep-1/'
        )
        self.pep2.owners.add(self.owner2)
        self.pep2.owners.add(self.owner3)

    def test_list_view(self):
        """ Setup some PEPs for testing """
        owner_string = self.pep2.get_owner_names()
        self.assertTrue('Jeff Triplett' in owner_string)
        self.assertTrue('Jacob Kaplan-Moss' in owner_string)

        self.assertEqual(self.owner1.email_display(), 'frank at revsys.com')

        # Simple view tests
        response = self.client.get(reverse('pep_list'))
        context = response.context

        self.assertTrue(self.cat1 in context['categories'])
        self.assertTrue(self.cat2 in context['categories'])
        self.assertTrue(self.cat3 in context['categories'])

        self.assertTrue(self.owner1 in context['owners'])
        self.assertTrue(self.owner2 in context['owners'])
        self.assertTrue(self.owner3 in context['owners'])

        self.assertTrue(self.pep1 in context['peps'])
        self.assertTrue(self.pep2 in context['peps'])

    def test_latest_rss_feed(self):
        response = self.client.get(reverse('pep_rss'))
        self.assertEqual(response.status_code, 200)


    def test_api_views(self):
        response = self.client.get('/api/v1/peps/pep/', content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 2)

        response = self.client.get('/api/v1/peps/pep/%s/' % self.pep1.pk, content_type='application/json')
        self.assertEqual(response.status_code, 200)

