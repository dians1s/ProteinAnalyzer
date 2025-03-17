from django.urls import path
from .views import home, get_protein

urlpatterns = [
    path('', home, name='home'),
    path('api/protein/', get_protein, name='get_protein'),
]
