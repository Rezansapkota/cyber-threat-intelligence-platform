import re

from django.db import IntegrityError

from .models import NewsAlert


# Each keyword maps to the severity that should be assigned when it appears
# in an article title or summary.
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
    """Create stored alerts for every keyword found in fetched articles."""
    alerts = []
    for article in articles:
        # One article can produce multiple alerts when it mentions several
        # tracked attack types, such as phishing and credential theft together.
        for keyword, severity in extract_keywords(article).items():
            alert = _save_alert(article, keyword, severity)
            if alert:
                alerts.append(alert)
    return alerts


def extract_keywords(article):
    """Return matched cyber keywords and their mapped severities."""
    # Search both the headline and summary because feeds often put the useful
    # threat context in only one of those fields.
    text = f'{article.get("title", "")} {article.get("description", "")}'
    normalized_text = text.lower()
    matches = {}

    for keyword, severity in KEYWORD_RULES.items():
        # Word boundaries avoid partial matches, so "patch" does not match
        # unrelated words that merely contain those letters.
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, normalized_text):
            matches[keyword] = severity

    return matches


def _save_alert(article, keyword, severity):
    """Persist one alert when the article has enough identifying data."""
    # A URL and title are the minimum fields needed to identify and display
    # a news alert in the dashboard.
    if not article.get('url') or not article.get('title'):
        return None

    try:
        # The model constraint keeps the same keyword/article pair from being
        # stored twice when feeds are refreshed.
        alert, _ = NewsAlert.objects.get_or_create(
            keyword=keyword,
            article_url=article['url'],
            defaults={
                # Database field lengths are enforced here so long feed values
                # do not break saves.
                'article_title': article['title'][:240],
                'source': article.get('source', '')[:120],
                'severity': severity,
                'summary': article.get('description', '')[:500],
            },
        )
        return alert
    except IntegrityError:
        # If two requests save the same alert at the same time, ignore the
        # duplicate instead of failing the feed refresh.
        return None
