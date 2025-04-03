from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView 


urlpatterns = [
    
    path('', RedirectView.as_view(url='welcome/', permanent=False)),
    path('', include('scraper.urls'))
    
]