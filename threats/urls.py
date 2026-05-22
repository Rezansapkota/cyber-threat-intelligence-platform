from django.urls import path

from . import views


# Public app routes; each page requires login in its view.
urlpatterns = [
    # Dashboard landing page.
    path('', views.index, name='index'),
    # Chart-heavy analysis pages.
    path('analytics/', views.analytics, name='analytics'),
    path('predictions/', views.predictions, name='predictions'),
    # Keyword-specific alert drilldown.
    path('categories/<slug:category_slug>/', views.category, name='category'),
    # Human-readable news page and JSON feed endpoint.
    path('news/', views.news, name='news'),
    path('news/feed/', views.news_feed, name='news_feed'),
]
