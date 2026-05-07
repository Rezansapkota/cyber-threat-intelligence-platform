from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import NewsAlert
from .news import _clean_summary
from .nlp import extract_keywords, process_news_articles


class ThreatIndexViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='analyst',
            password='strong-test-password',
        )
        self.client.login(username='analyst', password='strong-test-password')

    def test_anonymous_user_redirects_to_login(self):
        self.client.logout()

        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    @override_settings(CYBER_NEWS_FEEDS=[])
    def test_index_renders_nlp_dashboard(self):
        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Natural language processing dashboard')
        self.assertContains(response, 'Attack Keywords')
        self.assertContains(response, reverse('news'))
        self.assertContains(response, reverse('analytics'))

    @override_settings(CYBER_NEWS_FEEDS=[])
    def test_index_lists_news_alerts(self):
        NewsAlert.objects.create(
            keyword='ransomware',
            article_title='Ransomware campaign targets hospitals',
            article_url='https://example.com/ransomware',
            source='Example Feed',
            severity=NewsAlert.SEVERITY_CRITICAL,
            summary='Hospitals report active encryption attempts.',
        )

        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Live Alert Dashboard')
        self.assertContains(response, 'ransomware')
        self.assertContains(response, 'Critical alert')

    @override_settings(CYBER_NEWS_FEEDS=[])
    def test_index_shows_dashboard_charts(self):
        NewsAlert.objects.create(
            keyword='malware',
            article_title='Malware targets developers',
            article_url='https://example.com/malware',
            source='Example Feed',
            severity=NewsAlert.SEVERITY_HIGH,
        )
        NewsAlert.objects.create(
            keyword='vulnerability',
            article_title='Critical vulnerability exploited',
            article_url='https://example.com/vulnerability',
            source='Example Feed',
            severity=NewsAlert.SEVERITY_CRITICAL,
        )

        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Attack Types Ongoing')
        self.assertContains(response, 'Alert Severity')
        self.assertContains(response, 'Malware')
        self.assertContains(response, 'Vulnerability')
        self.assertContains(response, 'Total News Alerts')
        self.assertContains(response, reverse('category', args=['malware']))

    @override_settings(CYBER_NEWS_FEEDS=[])
    def test_news_feed_returns_json(self):
        response = self.client.get(reverse('news_feed'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'articles': [], 'error': ''})

    @override_settings(CYBER_NEWS_FEEDS=[])
    def test_news_page_renders(self):
        response = self.client.get(reverse('news'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cybersecurity News')
        self.assertContains(response, 'No cybersecurity news found right now.')

    @override_settings(CYBER_NEWS_FEEDS=[])
    def test_analytics_page_shows_metrics_and_predictions(self):
        NewsAlert.objects.create(
            keyword='malware',
            article_title='Malware targets developers',
            article_url='https://example.com/malware-one',
            source='Example Feed',
            severity=NewsAlert.SEVERITY_HIGH,
        )
        NewsAlert.objects.create(
            keyword='malware',
            article_title='Malware campaign expands',
            article_url='https://example.com/malware-two',
            source='Example Feed',
            severity=NewsAlert.SEVERITY_HIGH,
        )

        response = self.client.get(reverse('analytics'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Attack Analytics')
        self.assertContains(response, 'Attack Intensity Spider Web')
        self.assertContains(response, 'Upcoming Attack Prediction')
        self.assertContains(response, 'Malware')
        self.assertContains(response, 'High likelihood')

    def test_anonymous_analytics_redirects_to_login(self):
        self.client.logout()

        response = self.client.get(reverse('analytics'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_login_page_renders(self):
        self.client.logout()

        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign In')

    @override_settings(CYBER_NEWS_FEEDS=[])
    def test_category_page_lists_matching_alerts(self):
        NewsAlert.objects.create(
            keyword='malware',
            article_title='Malware targets developers',
            article_url='https://example.com/malware',
            source='Example Feed',
            severity=NewsAlert.SEVERITY_HIGH,
        )
        NewsAlert.objects.create(
            keyword='ransomware',
            article_title='Ransomware targets hospitals',
            article_url='https://example.com/ransomware',
            source='Example Feed',
            severity=NewsAlert.SEVERITY_CRITICAL,
        )

        response = self.client.get(reverse('category', args=['malware']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Malware Alerts')
        self.assertContains(response, 'Malware targets developers')
        self.assertNotContains(response, 'Ransomware targets hospitals')


class NewsNlpTests(TestCase):
    def test_extract_keywords_finds_important_terms(self):
        article = {
            'title': 'Ransomware gang exploits zero-day vulnerability',
            'description': 'Security teams are warned about malware delivery.',
        }

        keywords = extract_keywords(article)

        self.assertEqual(keywords['ransomware'], NewsAlert.SEVERITY_CRITICAL)
        self.assertEqual(keywords['zero-day'], NewsAlert.SEVERITY_CRITICAL)
        self.assertEqual(keywords['malware'], NewsAlert.SEVERITY_HIGH)

    def test_process_news_articles_saves_alerts_once(self):
        article = {
            'title': 'Phishing campaign steals credentials',
            'url': 'https://example.com/phishing',
            'source': 'Example Feed',
            'description': 'Credential theft observed in email attacks.',
        }

        process_news_articles([article])
        process_news_articles([article])

        self.assertEqual(NewsAlert.objects.count(), 2)
        self.assertTrue(
            NewsAlert.objects.filter(keyword='phishing').exists()
        )
        self.assertTrue(
            NewsAlert.objects.filter(keyword='credential theft').exists()
        )


class NewsFeedParsingTests(TestCase):
    def test_clean_summary_removes_html_and_limits_length(self):
        raw_summary = '<p><strong>Summary</strong></p>' + (' vulnerability' * 80)

        summary = _clean_summary(raw_summary, max_length=80)

        self.assertNotIn('<p>', summary)
        self.assertNotIn('<strong>', summary)
        self.assertLessEqual(len(summary), 83)
        self.assertNotIn('Summary', summary)
        self.assertIn('vulnerability', summary)
