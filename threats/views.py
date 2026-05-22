import math

from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.text import slugify

from .models import NewsAlert
from .news import fetch_cybersecurity_news
from .nlp import extract_keywords, process_news_articles


@login_required
def index(request):
    """Render the main dashboard with alert, keyword, and source totals."""
    news_alerts = NewsAlert.objects.all()
    # Group stored alerts by keyword/source so templates can draw charts
    # without doing database work.
    attack_stats = _chart_stats(
        news_alerts.values('keyword').annotate(count=Count('id')).order_by('-count'),
        'keyword',
    )
    source_stats = _chart_stats(
        news_alerts.values('source').annotate(count=Count('id')).order_by('-count'),
        'source',
    )
    category_links = _category_links()

    return render(
        request,
        'threats/index.html',
        {
            'attack_stats': attack_stats,
            'category_links': category_links,
            'news_alerts': news_alerts[:12],
            'source_stats': source_stats[:5],
            'total_alerts': news_alerts.count(),
        },
    )


@login_required
def news(request):
    """Fetch current cybersecurity news and display extracted keywords."""
    articles, error = fetch_cybersecurity_news()
    # Persist any matched keywords first, then attach keyword labels for the
    # article cards rendered on this request.
    process_news_articles(articles)
    for article in articles:
        article['keywords'] = extract_keywords(article).keys()

    return render(
        request,
        'threats/news.html',
        {
            'category_links': _category_links(),
            'news_articles': articles,
            'news_error': error,
        },
    )


@login_required
def category(request, category_slug):
    """Show stored alerts for one keyword category."""
    # Slugs are display-friendly URLs; convert them back before filtering the
    # database because keywords may contain spaces or punctuation.
    keyword = _keyword_from_slug(category_slug)
    alerts = NewsAlert.objects.filter(keyword=keyword) if keyword else NewsAlert.objects.none()
    severity_stats = _chart_stats(
        alerts.values('severity').annotate(count=Count('id')).order_by('-count'),
        'severity',
    )

    return render(
        request,
        'threats/category.html',
        {
            'alerts': alerts,
            'category_links': _category_links(),
            'category_name': keyword.replace('-', ' ').title() if keyword else category_slug.title(),
            'severity_stats': severity_stats,
            'total_alerts': alerts.count(),
        },
    )


@login_required
def analytics(request):
    """Render chart data for attack, severity, and source analytics."""
    news_alerts = NewsAlert.objects.all()
    # The analytics page uses the same grouped data in several chart formats.
    attack_stats = _chart_stats(
        news_alerts.values('keyword').annotate(count=Count('id')).order_by('-count'),
        'keyword',
    )
    severity_stats = _chart_stats(
        news_alerts.values('severity').annotate(count=Count('id')).order_by('-count'),
        'severity',
    )
    source_stats = _chart_stats(
        news_alerts.values('source').annotate(count=Count('id')).order_by('-count'),
        'source',
    )

    return render(
        request,
        'threats/analytics.html',
        {
            'attack_stats': attack_stats,
            'attack_pie_segments': _pie_segments(attack_stats[:6]),
            'category_links': _category_links(),
            'radar_labels': _radar_labels(attack_stats[:5]),
            'radar_points': _radar_points(attack_stats[:5]),
            'severity_stats': severity_stats,
            'source_stats': source_stats[:6],
            'total_alerts': news_alerts.count(),
        },
    )


@login_required
def predictions(request):
    """Show simple attack risk predictions based on stored alert history."""
    news_alerts = NewsAlert.objects.all()
    # Predictions are intentionally lightweight: they rank repeated/high
    # severity mentions rather than trying to forecast from external data.
    predictions_data = _attack_predictions(news_alerts)

    return render(
        request,
        'threats/predictions.html',
        {
            'category_links': _category_links(),
            'predictions': predictions_data,
            'total_alerts': news_alerts.count(),
        },
    )


@login_required
def news_feed(request):
    """Return fetched cybersecurity news as JSON for lightweight clients."""
    articles, error = fetch_cybersecurity_news()
    # Keep the database in sync even when news is fetched through JSON.
    process_news_articles(articles)
    return JsonResponse(
        {
            'articles': articles,
            'error': error,
        }
    )


def _chart_stats(rows, label_key):
    """Convert grouped query rows into reusable chart percentages."""
    rows = list(rows)
    # Percent values are relative to the largest group so bar charts scale
    # cleanly even when total alert volume is small.
    largest = max([row['count'] for row in rows], default=0)
    stats = []

    for row in rows:
        label = row[label_key]
        stats.append(
            {
                'label': label,
                'label_display': label.replace('-', ' ').title(),
                'slug': slugify(label),
                'count': row['count'],
                'percent': round((row['count'] / largest) * 100) if largest else 0,
            }
        )

    return stats


def _category_links():
    """Build keyword category links ordered by alert volume."""
    # These links power the shared "Attack Categories" menu across pages.
    rows = (
        NewsAlert.objects.values('keyword')
        .annotate(count=Count('id'))
        .order_by('-count', 'keyword')
    )
    return [
        {
            'name': row['keyword'].replace('-', ' ').title(),
            'slug': slugify(row['keyword']),
            'count': row['count'],
        }
        for row in rows
    ]


def _keyword_from_slug(category_slug):
    """Resolve a URL slug back to its stored keyword value."""
    # Compare slugified values so URLs remain stable for keywords like
    # "data breach" and "zero-day".
    for keyword in NewsAlert.objects.values_list('keyword', flat=True).distinct():
        if slugify(keyword) == category_slug:
            return keyword
    return ''


def _radar_labels(stats):
    """Place labels around the SVG radar chart."""
    label_points = []
    count = len(stats)
    if not count:
        return label_points

    for index, stat in enumerate(stats):
        x, y = _radar_coordinate(index, count, 96)
        label_points.append(
            {
                'label': stat['label_display'],
                'x': x,
                'y': y,
            }
        )
    return label_points


def _radar_points(stats):
    """Build SVG polygon points for the radar chart."""
    count = len(stats)
    if not count:
        return ''

    largest = max([stat['count'] for stat in stats], default=1)
    points = []
    for index, stat in enumerate(stats):
        # Larger counts sit farther from the center, making stronger attack
        # categories visually stand out.
        radius = 70 * (stat['count'] / largest)
        x, y = _radar_coordinate(index, count, radius)
        points.append(f'{x},{y}')

    return ' '.join(points)


def _radar_coordinate(index, count, radius):
    """Calculate one point on a centered radar chart circle."""
    angle = (2 * math.pi * index / count) - (math.pi / 2)
    x = round(100 + radius * math.cos(angle), 2)
    y = round(100 + radius * math.sin(angle), 2)
    return x, y


def _pie_segments(stats):
    """Convert top attack stats into colored pie chart segments."""
    total = sum(stat['count'] for stat in stats)
    if not total:
        return []

    palette = ['#52677a', '#b89d6a', '#7a8c99', '#8f7560', '#9aa8b5', '#6f7f72']
    start = 0
    segments = []
    for index, stat in enumerate(stats):
        # SVG pie slices are described as start/end angles in degrees.
        degrees = round((stat['count'] / total) * 360, 2)
        end = start + degrees
        segments.append(
            {
                'color': palette[index % len(palette)],
                'count': stat['count'],
                'end': round(end, 2),
                'label': stat['label_display'],
                'percent': round((stat['count'] / total) * 100),
                'start': round(start, 2),
            }
        )
        start = end

    return segments


def _attack_predictions(alerts):
    """Rank attack types with a small severity-weighted scoring model."""
    # Critical alerts contribute the most because they usually represent
    # active exploitation or high-impact incidents.
    severity_weight = {
        NewsAlert.SEVERITY_CRITICAL: 3,
        NewsAlert.SEVERITY_HIGH: 2,
        NewsAlert.SEVERITY_MEDIUM: 1,
    }
    scores = {}

    for alert in alerts:
        # Accumulate one score bucket per attack keyword.
        scores.setdefault(
            alert.keyword,
            {
                'keyword': alert.keyword,
                'label': alert.keyword.replace('-', ' ').title(),
                'score': 0,
                'count': 0,
                'critical': 0,
                'high': 0,
            },
        )
        scores[alert.keyword]['score'] += severity_weight.get(alert.severity, 1)
        scores[alert.keyword]['count'] += 1
        if alert.severity == NewsAlert.SEVERITY_CRITICAL:
            scores[alert.keyword]['critical'] += 1
        if alert.severity == NewsAlert.SEVERITY_HIGH:
            scores[alert.keyword]['high'] += 1

    # Sort by total score first, then use severe alert counts as tie-breakers.
    predictions = sorted(
        scores.values(),
        key=lambda item: (item['score'], item['critical'], item['high'], item['count']),
        reverse=True,
    )

    for prediction in predictions:
        # Convert the numeric score into simple analyst-facing risk language.
        if prediction['critical']:
            prediction['risk'] = 'High'
            prediction['reason'] = 'Critical alerts are already present for this attack type.'
        elif prediction['high'] >= 2:
            prediction['risk'] = 'High'
            prediction['reason'] = 'Multiple high severity alerts suggest continued activity.'
        elif prediction['count'] >= 2:
            prediction['risk'] = 'Medium'
            prediction['reason'] = 'Repeated mentions suggest this attack type is active.'
        else:
            prediction['risk'] = 'Watch'
            prediction['reason'] = 'Detected in current news, but with limited supporting alerts.'

    predictions = predictions[:5]
    largest_score = max([prediction['score'] for prediction in predictions], default=1)
    for index, prediction in enumerate(predictions, start=1):
        # Percent and ray index are presentation values used by the gauge UI.
        prediction['percent'] = round((prediction['score'] / largest_score) * 100)
        prediction['ray_index'] = index

    return predictions
