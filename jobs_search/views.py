from array import array
from multiprocessing import Array
from django.shortcuts import render
from django.views.generic import ListView
from .models import Jobs
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchVector, SearchQuery

import datetime
import re
import json
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict

# Create your views here.


def index(request):
    template_name = 'jobs_search/index.html'

    context = {
        'judul': 'Welcome Jobsearch',
        'keywordTitle': request.GET.get('keywordTitle'),
        'keywordLocation': request.GET.get('keywordLocation'),
    }
    return render(request, template_name, context)


def get_data(request):
    jobs_list = Jobs.objects.all()
    jobs_count = Jobs.objects.count()

    keyword = request.GET.get('keyword')
    keywordTitle = request.GET.get('keywordTitle')
    keywordLocation = request.GET.get('keywordLocation')

    # dateFrom = request.GET.get('dateFrom')
    # dateTo = request.GET.get('dateTo')

    now = datetime.date.today()
    yesterday = now - datetime.timedelta(days=1)
    last_3_day = now - datetime.timedelta(days=3)
    last_7_day = now - datetime.timedelta(days=7)

    # Pattern regex ini berfungsi untuk melakukan matching dengan data dalam database
    # Misal data yang ingin dicari adalah Yogyakarta pada field lokasi dengan menginputkan keyword "Yog", maka pattern regex tersebut akan mencari kata "Yog" dengan case-insensitive menyesuaikan data dalam database
    re_pattern_matching = r"(?i).*"

    if keyword:
        jobs_list = Jobs.objects.annotate(search=SearchVector("title", "location", "requirement")).filter(
            search=SearchQuery(keyword)).order_by('-datetime_posted')
        jobs_count = jobs_list.count()
        # jobs_list = Jobs.objects.annotate(search=SearchVector("title","location")).filter(search=SearchQuery(r"(?i).*"+keyword)).order_by('-datetime_posted')
        # jobs_count = Jobs.objects.annotate(search=SearchVector("title","location")).filter(search=SearchQuery(r"(?i).*"+keyword)).count()

    if keywordTitle and keywordLocation:
        jobs_list = Jobs.objects.filter(Q(title__iregex=re_pattern_matching+keywordTitle) & Q(
            location__iregex=re_pattern_matching+keywordLocation)).order_by('-datetime_posted')
        jobs_count = jobs_list.count()
    elif keywordTitle:
        jobs_list = Jobs.objects.filter(
            Q(title__iregex=re_pattern_matching+keywordTitle)).order_by('-datetime_posted')
        jobs_count = jobs_list.count()
    elif keywordLocation:
        jobs_list = Jobs.objects.filter(
            Q(location__iregex=re_pattern_matching+keywordLocation)).order_by('-datetime_posted')
        jobs_count = jobs_list.count()

    paginator = Paginator(jobs_list, 16)
    page = request.GET.get('page')
    jobs = paginator.get_page(page)

    try:
        jobs = paginator.page(page)
    except PageNotAnInteger:
        jobs = paginator.page(1)
    except EmptyPage:
        jobs = paginator.page(paginator.num_pages)

    data = list(Jobs.objects.values())
    context = {
        'jobs': jobs,
        'jobslist': JsonResponse(data, safe=False),
        'keyword': keyword,
        'keywordTitle': keywordTitle,
        'keywordLocation': keywordLocation,
        'jobs_count': jobs_count,
        'last_3_day': last_3_day,

    }
    return context


def search_jobs(request):
    template_name = 'jobs_search/jobs_list.html'
    context = get_data(request)

    return render(request, template_name, context)


jobs_list = ''
jobs_count = ''


@csrf_exempt
def jobs_api(request):
    keywordTitle = request.POST.get('keywordTitle')
    keywordLocation = request.POST.get('keywordLocation')

    re_pattern_matching = r"(?i).*"

    global jobs_list
    global jobs_count

    if keywordTitle and keywordLocation:
        jobs_list = Jobs.objects.filter(Q(title__iregex=re_pattern_matching+keywordTitle) & Q(
            location__iregex=re_pattern_matching+keywordLocation)).order_by('-datetime_posted')
        jobs_count = jobs_list.count()
    elif keywordTitle:
        jobs_list = Jobs.objects.filter(
            Q(title__iregex=re_pattern_matching+keywordTitle)).order_by('-datetime_posted')
        jobs_count = jobs_list.count()
    elif keywordLocation:
        jobs_list = Jobs.objects.filter(
            Q(location__iregex=re_pattern_matching+keywordLocation)).order_by('-datetime_posted')
        jobs_count = jobs_list.count()
    else:
        jobs_list = Jobs.objects.all()
        jobs_count = jobs_list.count()

    datas = []
    for dt in jobs_list.iterator():
        data_list = model_to_dict(dt)
        link = data_list['link']
        # jobsite = re.match(r"jobsite", link).group()
        jobsite = re.sub(r"(.co.id|.com)(.*)", r"", re.sub(r"https://www.", r"", link)).title()
        data = {
            'title'           : data_list['title'],
            'image'           : data_list['image'],
            'company'         : data_list['company'],
            'location'        : data_list['location'],
            'requirement'     : data_list['requirement'],
            'datetime_posted' : 'Posted ' + str(data_list['datetime_posted']) + " by " + jobsite,
            'link'            : link,
        }
        datas.append(data)
        
    return HttpResponse(json.dumps(datas, default=str), content_type="application/json")

    # jobs_json = serializers.serialize('json', jobs_list)
    # return HttpResponse(jobs_json, content_type="application/json")