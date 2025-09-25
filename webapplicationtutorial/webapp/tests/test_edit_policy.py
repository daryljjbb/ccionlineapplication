from django.test import TestCase
from django.urls import reverse
from webapp.models import Customer, Carrier, Policy
from django.contrib.auth.models import User
import json


class EditPolicyViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.customer = Customer.objects.create(first_name='John', last_name='Doe', email='john@example.com')
        self.carrier = Carrier.objects.create(name='ACME', is_active=True)
        self.policy = Policy.objects.create(
            customer=self.customer,
            carrier=self.carrier,
            policy_number='P-100',
            policy_type='home',
            effective_date='2024-01-01',
            expiration_date='2025-01-01',
            premium_amount=100.00,
            agency_fee=10.00,
            status='active',
            details={
                'property_address': '123 Main St',
                'year_built': 1990,
                'square_footage': 1800,
                'deductible': '1000',
                'wind_deductible': '2000',
                'coverages': {
                    'dwelling': {'limit': '250000', 'premium': '500.00'},
                    'other_structures': {'limit': '50000', 'premium': '50.00'},
                }
            }
        )

    def test_policy_details_json_present_and_form_prefilled(self):
        url = reverse('edit_policy', args=[self.policy.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check context contains policy_details_json
        self.assertIn('policy_details_json', response.context)
        details = json.loads(response.context['policy_details_json'])
        self.assertEqual(details['property_address'], '123 Main St')
        # Ensure rendered HTML contains property address in textarea value
        self.assertContains(response, '123 Main St')

    def test_edit_policy_post_updates_details(self):
        """POST updated homeowner fields to edit_policy and assert details updated."""
        url = reverse('edit_policy', args=[self.policy.id])
        post_data = {
            'carrier': str(self.carrier.id),
            'policy_number': self.policy.policy_number,
            'effective_date': '2024-01-01',
            'expiration_date': '2025-01-01',
            'premium_amount': '100.00',
            'agency_fee': '10.00',
            'status': 'active',
            # Home-specific fields
            'property_address': '456 New Ave',
            'year_built': '2000',
            'square_footage': '2200',
            'dwelling_limit': '300000',
            'dwelling_premium': '600.00',
            'other_structures_limit': '60000',
            'other_structures_premium': '60.00',
            'personal_property_limit': '',
            'personal_property_premium': '0.00',
            'loss_of_use_limit': '',
            'loss_of_use_premium': '0.00',
            'personal_liability_limit': '',
            'personal_liability_premium': '0.00',
            'medical_payments_limit': '',
            'medical_payments_premium': '0.00',
            'deductible': '1500',
            'wind_deductible': '2500',
            'total_customer_cost': '660.00',
        }

        response = self.client.post(url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Refresh from DB and check details
        self.policy.refresh_from_db()
        self.assertEqual(self.policy.details.get('property_address'), '456 New Ave')
        self.assertEqual(str(self.policy.details.get('year_built')), '2000')
        self.assertIn('coverages', self.policy.details)
        self.assertEqual(self.policy.details['coverages']['dwelling']['premium'], '600.00')
        # total_customer_cost should be saved (stringified Decimal)
        self.assertEqual(self.policy.details.get('total_customer_cost'), '660.00')
        

class ReplaceFilterTests(TestCase):
    def test_replace_filter_safe(self):
        from django.template import Template, Context
        t = Template("{% load webapp_extras %}{{ 'a_b'|replace:'_, ' }}")
        rendered = t.render(Context())
        # The filter replaces '_' with ' ' when given '_, ' so expect 'a b'
        self.assertIn('a b', rendered)


class PolicyTotalTests(TestCase):
    def test_total_customer_cost_property(self):
        from decimal import Decimal
        customer = Customer.objects.create(first_name='Jane', last_name='Smith', email='jane@example.com')
        carrier = Carrier.objects.create(name='ACME2', is_active=True)
        policy = Policy.objects.create(
            customer=customer,
            carrier=carrier,
            policy_number='P-200',
            policy_type='home',
            effective_date='2024-01-01',
            expiration_date='2025-01-01',
            premium_amount=100.00,
            agency_fee=10.00,
            status='active',
        )
        # setter accepts Decimal and stores string in details
        policy.total_customer_cost = Decimal('110.00')
        policy.save()
        policy.refresh_from_db()
        self.assertEqual(str(policy.total_customer_cost), '110.00')
        # set None clears it
        policy.total_customer_cost = None
        policy.save()
        policy.refresh_from_db()
        self.assertIsNone(policy.total_customer_cost)
