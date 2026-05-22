from django.db import models


class Threat(models.Model):
    """Manual threat record stored by analysts."""

    SEVERITY_LOW = 'low'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CRITICAL = 'critical'

    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    title = models.CharField(max_length=160)
    source = models.CharField(max_length=120, blank=True)
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_MEDIUM,
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        """Show the threat title in admin and shell output."""
        return self.title


class NewsAlert(models.Model):
    """Threat alert created from cybersecurity news keywords."""

    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CRITICAL = 'critical'

    SEVERITY_CHOICES = [
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    keyword = models.CharField(max_length=80)
    article_title = models.CharField(max_length=240)
    article_url = models.URLField()
    source = models.CharField(max_length=120)
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_MEDIUM,
    )
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['keyword', 'article_url'],
                name='unique_keyword_per_article',
            ),
        ]

    def __str__(self):
        """Show the matched keyword beside the source article title."""
        return f'{self.keyword}: {self.article_title}'
