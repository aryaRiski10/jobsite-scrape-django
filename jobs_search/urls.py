from django.urls import path, re_path
from django.views.generic import ListView
# from .views import JobsListView
from . import views
from .models import Jobs

app_name = 'jobs-search'
urlpatterns =[
    path('', views.index, name='index'),
    path('jobs-search/', views.search_jobs, name='job_list'),
    path('jobs-search-api/', views.jobs_api, name='jobs_api'),

]