from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('analytics/', views.analytics, name='analytics'),
    path('predictions/', views.predictions, name='predictions'),
    path('categories/<slug:category_slug>/', views.category, name='category'),
    path('news/', views.news, name='news'),
    path('news/feed/', views.news_feed, name='news_feed'),
]
