from email.utils import parsedate_to_datetime
from html import unescape
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from django.conf import settings


def fetch_cybersecurity_news():
    articles = []
    errors = []

    for feed in settings.CYBER_NEWS_FEEDS:
        try:
            articles.extend(_fetch_feed(feed['name'], feed['url']))
        except HTTPError as error:
            errors.append(f'{feed["name"]} ({error.code})')
        except (ET.ParseError, URLError, TimeoutError) as error:
            errors.append(f'{feed["name"]} ({error.__class__.__name__})')

    articles.sort(key=lambda article: article['published_sort'], reverse=True)
    error = ''
    if errors:
        error = f'Could not load news from: {", ".join(errors)}.'

    return articles[:18], error


def _fetch_feed(source_name, feed_url):
    request = Request(
        feed_url,
        headers={'User-Agent': 'cyber-threat-intelligence-platform/1.0'},
    )
    with urlopen(request, timeout=8) as response:
        root = ET.fromstring(response.read())

    if root.tag.endswith('rss'):
        return _parse_rss(source_name, root)

    return _parse_atom(source_name, root)


def _parse_rss(source_name, root):
    articles = []
    for item in root.findall('./channel/item')[:6]:
        published = _text(item, 'pubDate')
        articles.append(
            {
                'title': _text(item, 'title'),
                'url': _text(item, 'link'),
                'source': source_name,
                'published_at': published,
                'published_sort': _published_sort(published),
                'description': _clean_summary(_text(item, 'description')),
            }
        )
    return articles


def _parse_atom(source_name, root):
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    articles = []
    for entry in root.findall('atom:entry', namespace)[:6]:
        link = entry.find('atom:link[@rel="alternate"]', namespace)
        published = _atom_text(entry, 'published', namespace) or _atom_text(
            entry,
            'updated',
            namespace,
        )
        articles.append(
            {
                'title': _atom_text(entry, 'title', namespace),
                'url': link.get('href', '') if link is not None else '',
                'source': source_name,
                'published_at': published,
                'published_sort': _published_sort(published),
                'description': _clean_summary(_atom_text(entry, 'summary', namespace)),
            }
        )
    return articles


def _text(element, child_name):
    child = element.find(child_name)
    return child.text.strip() if child is not None and child.text else ''


def _atom_text(element, child_name, namespace):
    child = element.find(f'atom:{child_name}', namespace)
    return child.text.strip() if child is not None and child.text else ''


def _published_sort(value):
    if not value:
        return ''

    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError):
        return value


def _clean_summary(value, max_length=420):
    if not value:
        return ''

    text = re.sub(r'<[^>]+>', ' ', value)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^(View CSAF\s*)?(Summary\s*)+', '', text, flags=re.IGNORECASE)

    if len(text) <= max_length:
        return text

    return f'{text[:max_length].rsplit(" ", 1)[0]}...'
