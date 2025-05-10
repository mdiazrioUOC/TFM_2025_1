"""
URL configuration for clinical_annotator project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from notes import views
from django.urls import path
from django.contrib import admin
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/add-clinical-note/', permanent=False)),
    path('add-clinical-note/', views.add_clinical_note, name='add_clinical_note'),
    path('clinical-note-processed/', views.clinical_note_processed, name='clinical_note_processed'),
    path('delete-hpo-code/', views.delete_hpo_code, name='delete_hpo_code'),
    path('exchange-hpo-code/', views.exchange_hpo_code, name='exchange_hpo_code'),
    path('add-hpo-code/', views.add_hpo_code, name='add_hpo_code'),
    path('api/search-hpo/', views.search_hpo_terms, name='search_hpo_terms'),
]