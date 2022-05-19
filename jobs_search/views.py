from array import array
from multiprocessing import Array
from django.shortcuts import render
from django.views.generic import ListView
from .models import Jobs
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.template.defaultfilters import linebreaksbr
from django.template.loader import render_to_string
from django.utils import formats

import datetime
import re
import json

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

    page = request.GET.get('page')
    keywordTitle = request.GET.get('keywordTitle')
    keywordLocation = request.GET.get('keywordLocation')

    now = datetime.date.today()
    yesterday = now - datetime.timedelta(days=1)
    last_3_day = now - datetime.timedelta(days=3)
    last_7_day = now - datetime.timedelta(days=7)

    categories =  [
            ['jobstreet','Jobstreet'],
            ['kalibrr','Kalibrr'],
            ['glints','Glints']
    ]
    
    # Pattern regex ini berfungsi untuk melakukan matching dengan data dalam database
    # Misal data yang ingin dicari adalah Yogyakarta pada field lokasi dengan menginputkan keyword "Yog", maka pattern regex tersebut akan mencari kata "Yog" dengan case-insensitive menyesuaikan data dalam database
    re_pattern_matching = r"(?i).*"

    # if keyword:
    #     jobs_list = Jobs.objects.annotate(search=SearchVector("title", "location", "requirement")).filter(
    #         search=SearchQuery(keyword)).order_by('-datetime_posted')
    #     jobs_count = jobs_list.count()
    #     # jobs_list = Jobs.objects.annotate(search=SearchVector("title","location")).filter(search=SearchQuery(r"(?i).*"+keyword)).order_by('-datetime_posted')
    #     # jobs_count = Jobs.objects.annotate(search=SearchVector("title","location")).filter(search=SearchQuery(r"(?i).*"+keyword)).count()

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
        'page': page,
        'keywordTitle': keywordTitle,
        'keywordLocation': keywordLocation,
        'jobs_count': jobs_count,
        'last_3_day': last_3_day,
        'categories' : categories

    }
    return context


def search_jobs(request):
    template_name = 'jobs_search/jobs_list.html'
    context = get_data(request)

    return render(request, template_name, context)


# ----------------------api------------------------
jobs_list = ''
jobs_count = ''

@csrf_exempt
def jobs_api(request):
    keywordTitle    = request.POST.get('keywordTitle')
    keywordLocation = request.POST.get('keywordLocation')

    check_hari_1  = request.POST.get('check_hari_1') == 'true'
    check_hari_3  = request.POST.get('check_hari_3') == 'true'
    check_hari_14 = request.POST.get('check_hari_14') == 'true'
    check_hari_30 = request.POST.get('check_hari_30') == 'true'

    cat_jobstreet = request.POST.get('cat_jobstreet') == 'true'
    cat_kalibrr   = request.POST.get('cat_kalibrr') == 'true'
    cat_glints    = request.POST.get('cat_glints') == 'true'

    re_pattern_matching = r"(?i).*"

    global jobs_list
    global jobs_count
    
    now         = datetime.date.today()
    yesterday   = now - datetime.timedelta(days=1)
    last_3_day  = now - datetime.timedelta(days=4)
    last_14_day = now - datetime.timedelta(days=14)
    last_30_day = now - datetime.timedelta(days=30)

    if keywordTitle and keywordLocation:
        jobs_list = Jobs.objects.filter(Q(title__iregex=re_pattern_matching+keywordTitle) & Q(
            location__iregex=re_pattern_matching+keywordLocation))
        jobs_count = jobs_list.count()
    elif keywordTitle:
        jobs_list = Jobs.objects.filter(
            Q(title__iregex=re_pattern_matching+keywordTitle))
        jobs_count = jobs_list.count()
    elif keywordLocation:
        jobs_list = Jobs.objects.filter(
            Q(location__iregex=re_pattern_matching+keywordLocation))
        jobs_count = jobs_list.count()
    else:
        jobs_list = Jobs.objects.all()
        jobs_count = jobs_list.count()
    
    jobs_list = jobs_list.order_by('-datetime_posted')

    data = []
            
    i = 0;
    for dt in jobs_list.iterator():
        data_list = model_to_dict(dt)

        if (check_hari_30 and data_list['datetime_posted'] <= last_30_day):
            continue
        if (check_hari_14 and data_list['datetime_posted'] <= last_14_day):
            continue
        if (check_hari_3 and data_list['datetime_posted'] <= last_3_day):
            continue
        if (check_hari_1 and data_list['datetime_posted'] <= yesterday):
            continue

        link = data_list['link']
        jobsite = re.sub(r"(.co.id|.com)(.*)", r"", re.sub(r"https://www.", r"", link)).title()

        if (cat_jobstreet and jobsite != 'Jobstreet'):
            continue
        if (cat_kalibrr and jobsite != 'Kalibrr'):
            continue
        if (cat_glints and jobsite != 'Glints'):
            continue
        
        formatted_date = formats.date_format(data_list['datetime_posted'], "F, d Y")
        data_row = {
            'title'           : data_list['title'],
            'image'           : data_list['image'],
            'company'         : data_list['company'],
            'location'        : data_list['location'],
            'requirement'     : data_list['requirement'],
            'datetime_posted' : 'Posted ' + formatted_date + " by " + jobsite,
            'link'            : link,
            'detailModelId'   : 'detailModel-' + str(i),
        }
        data.append(data_row)
        i += 1 
    
    paginator = Paginator(data, 16)
    page = request.POST.get('page')
    jobs = paginator.get_page(page)
    try:
        jobs = paginator.page(page)
    except PageNotAnInteger:
        jobs = paginator.page(1)
    except EmptyPage:
        jobs = paginator.page(paginator.num_pages)
    
    paginate = render_to_string('jobs_search/paginator.html', {
        'keywordTitle': keywordTitle,
        'keywordLocation': keywordLocation,
        'jobs': jobs
    })
    
    context = {
        'data': jobs.object_list,
        'total': len(data),
        'paginator': paginate,
    }
    
    return HttpResponse(json.dumps(context, default=str), content_type="application/json")