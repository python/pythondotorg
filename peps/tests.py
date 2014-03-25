from django.test import TestCase
from django.core.management import call_command
from django.core.urlresolvers import reverse

from users.factories import StaffUserFactory

from . import admin # Coverage FTW
from .models import PepType, PepStatus, PepOwner, PepCategory, Pep

from .factories import (
    PepTypeFactory, PepStatusFactory, PepCategoryFactory, PepOwnerFactory,
    PepFactory
)

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


class PEPApiTests(TestCase):
    def setUp(self):
        self.pep_type = PepTypeFactory()
        self.pep_status = PepStatusFactory()
        self.pep_category = PepCategoryFactory()
        self.pep_owner = PepOwnerFactory()

        self.staff_user = StaffUserFactory()
        self.staff_key = self.staff_user.api_key.key
        self.Authorization = "ApiKey %s:%s" % (self.staff_user.username, self.staff_key)

    def json_client(self, method, url, data=None, **headers):
        if not data:
            data = {}
        client_method = getattr(self.client, method.lower())
        return client_method(url, json.dumps(data), content_type='application/json', **headers)

    # Pep
    def test_pep_list_get(self):
        PepFactory()
        PepFactory()
        response = self.client.get('/api/v1/peps/pep/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 2)

    def test_pep_detail_get(self):
        pep1 = PepFactory()
        response = self.client.get('/api/v1/peps/pep/%s/' % pep1.pk)
        self.assertEqual(response.status_code, 200)

    def test_pep_post(self):
        payload = {
            'type': '/api/v1/peps/type/%d/' % self.pep_type.pk,
            'status': '/api/v1/peps/status/%d/' % self.pep_status.pk,
            'category': '/api/v1/peps/category/%d/' % self.pep_category.pk,
            'title': 'First PEP ever',
            'number': 1,
            'owners': [
                '/api/v1/peps/owner/%d/' % self.pep_owner.pk
            ],
            'url': 'http://peps.org/1/',
        }
        response = self.json_client('post', '/api/v1/peps/pep/', payload, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 201)

    def test_pep_delete(self):
        pep1 = PepFactory()
        response = self.client.get('/api/v1/peps/pep/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 1)

        response = self.json_client('delete', '/api/v1/peps/pep/%d/' % pep1.pk, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/api/v1/peps/pep/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 0)

    # PepType
    def test_type_list_get(self):
        response = self.client.get('/api/v1/peps/type/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 1)

    def test_type_detail_get(self):
        response = self.client.get('/api/v1/peps/type/%d/' % self.pep_type.pk)
        self.assertEqual(response.status_code, 200)

    def test_type_post(self):
        payload = {
            'name': 'new',
            'abbreviation': 'NEW'
        }
        response = self.json_client('post', '/api/v1/peps/type/', payload, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 201)

    def test_type_delete(self):
        response = self.client.get('/api/v1/peps/type/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 1)

        response = self.json_client('delete', '/api/v1/peps/type/%d/' % self.pep_type.pk, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/api/v1/peps/type/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 0)

    # PepCategory
    def test_category_list_get(self):
        response = self.client.get('/api/v1/peps/category/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 1)

    def test_category_detail_get(self):
        response = self.client.get('/api/v1/peps/category/%d/' % self.pep_category.pk)
        self.assertEqual(response.status_code, 200)

    def test_category_post(self):
        payload = {
            'name': 'new',
            'abbreviation': 'NEW'
        }
        response = self.json_client('post', '/api/v1/peps/category/', payload, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 201)

    def test_category_delete(self):
        response = self.client.get('/api/v1/peps/category/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 1)

        response = self.json_client('delete', '/api/v1/peps/category/%d/' % self.pep_category.pk, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/api/v1/peps/category/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 0)

    # PepStatus
    def test_status_list_get(self):
        response = self.client.get('/api/v1/peps/status/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 1)

    def test_status_detail_get(self):
        response = self.client.get('/api/v1/peps/status/%d/' % self.pep_status.pk)
        self.assertEqual(response.status_code, 200)

    def test_status_post(self):
        payload = {
            'name': 'new',
            'abbreviation': 'NEW'
        }
        response = self.json_client('post', '/api/v1/peps/status/', payload, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 201)

    def test_status_delete(self):
        response = self.client.get('/api/v1/peps/status/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 1)

        response = self.json_client('delete', '/api/v1/peps/status/%d/' % self.pep_status.pk, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/api/v1/peps/status/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 0)

    # PepOwner
    def test_owner_list_get(self):
        response = self.client.get('/api/v1/peps/owner/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 1)

    def test_owner_detail_get(self):
        response = self.client.get('/api/v1/peps/owner/%d/' % self.pep_owner.pk)
        self.assertEqual(response.status_code, 200)

    def test_owner_post(self):
        payload = {
            'name': 'new',
            'abbreviation': 'NEW'
        }
        response = self.json_client('post', '/api/v1/peps/owner/', payload, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 201)

    def test_owner_delete(self):
        response = self.client.get('/api/v1/peps/owner/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 1)

        response = self.json_client('delete', '/api/v1/peps/owner/%d/' % self.pep_owner.pk, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/api/v1/peps/owner/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['objects']), 0)
