from django.test import TestCase
from django.urls import reverse

from .models import Threat


class ThreatIndexViewTests(TestCase):
    def test_index_lists_saved_threats(self):
        Threat.objects.create(
            title='Credential phishing campaign',
            source='SOC',
            severity=Threat.SEVERITY_HIGH,
            description='Observed against finance users.',
        )

        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Credential phishing campaign')
        self.assertContains(response, 'SOC')
        self.assertContains(response, 'High severity')

    def test_post_creates_threat(self):
        response = self.client.post(
            reverse('index'),
            {
                'title': 'Malware callback',
                'source': 'EDR',
                'severity': Threat.SEVERITY_CRITICAL,
                'description': 'Beaconing to suspicious infrastructure.',
            },
        )

        self.assertRedirects(response, reverse('index'))
        threat = Threat.objects.get(title='Malware callback')
        self.assertEqual(threat.source, 'EDR')
        self.assertEqual(threat.severity, Threat.SEVERITY_CRITICAL)
