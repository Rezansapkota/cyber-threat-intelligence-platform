import re

from django.db import IntegrityError

from .models import NewsAlert


KEYWORD_RULES = {
    'ransomware': NewsAlert.SEVERITY_CRITICAL,
    'malware': NewsAlert.SEVERITY_HIGH,
    'phishing': NewsAlert.SEVERITY_HIGH,
    'data breach': NewsAlert.SEVERITY_CRITICAL,
    'zero-day': NewsAlert.SEVERITY_CRITICAL,
    'vulnerability': NewsAlert.SEVERITY_HIGH,
    'exploit': NewsAlert.SEVERITY_HIGH,
    'credential theft': NewsAlert.SEVERITY_HIGH,
    'botnet': NewsAlert.SEVERITY_HIGH,
    'spyware': NewsAlert.SEVERITY_HIGH,
    'trojan': NewsAlert.SEVERITY_HIGH,
    'ddos': NewsAlert.SEVERITY_MEDIUM,
    'patch': NewsAlert.SEVERITY_MEDIUM,
}


def process_news_articles(articles):
    alerts = []
    for article in articles:
        for keyword, severity in extract_keywords(article).items():
            alert = _save_alert(article, keyword, severity)
            if alert:
                alerts.append(alert)
    return alerts


def extract_keywords(article):
    text = f'{article.get("title", "")} {article.get("description", "")}'
    normalized_text = text.lower()
    matches = {}

    for keyword, severity in KEYWORD_RULES.items():
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, normalized_text):
            matches[keyword] = severity

    return matches


def _save_alert(article, keyword, severity):
    if not article.get('url') or not article.get('title'):
        return None

    try:
        alert, _ = NewsAlert.objects.get_or_create(
            keyword=keyword,
            article_url=article['url'],
            defaults={
                'article_title': article['title'][:240],
                'source': article.get('source', '')[:120],
                'severity': severity,
                'summary': article.get('description', '')[:500],
            },
        )
        return alert
    except IntegrityError:
        return None
