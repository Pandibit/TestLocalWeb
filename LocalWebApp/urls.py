from django.urls import path
from .views import user_stats

urlpatterns = [
    path('user-stats/<int:user_id>/', user_stats, name='user-stats'),
]