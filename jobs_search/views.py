from array import array
from functools import reduce
from multiprocessing import Array
from multiprocessing.sharedctypes import Value
import operator
from django.shortcuts import render
from django.views.generic import ListView
from .models import Jobs
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchHeadline, SearchRank, TrigramDistance
from django.utils import timezone
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.template.defaultfilters import linebreaksbr
from django.template.loader import render_to_string
from django.utils import formats
from django.db.models.expressions import Window
from django.db.models.functions import Rank

from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import nltk
nltk.download('punkt')

import datetime
import regex as re
import json

# Create your views here.


def index(request):
    template_name = 'jobs_search/index.html'

    context = {
        'judul': 'Welcome Jobsearch',
        'keyword': request.GET.get('keyword'),
        'klocation': request.GET.get('klocation'),
    }
    return render(request, template_name, context)


def get_data(request):
    jobs_list = Jobs.objects.all()
    jobs_count = Jobs.objects.count()

    page = request.GET.get('page')
    
    keyword = request.GET.get('keyword')
    klocation = request.GET.get('klocation')
    
    now = datetime.date.today()
    
    yesterday = now - datetime.timedelta(days=1)
    last_3_day = now - datetime.timedelta(days=3)
    last_7_day = now - datetime.timedelta(days=7)

    categories =  [
            ['jobstreet','Jobstreet'],
            ['kalibrr','Kalibrr'],
            ['glints','Glints']
    ]
    
    last_n_day =  [
            ['yesterday','1 Hari Terakhir'],
            ['last_3_day','3 Hari Terakhir'],
            ['last_14_day','14 Hari Terakhir'],
            ['last_30_day','30 Hari Terakhir']
    ]
    
    ordering = [
        ['relevance','Relevansi'],
        ['date','Tanggal']
    ]
    # Pattern regex ini berfungsi untuk melakukan matching dengan data dalam database
    # Misal data yang ingin dicari adalah Yogyakarta pada field lokasi dengan menginputkan keyword "Yog", maka pattern regex tersebut akan mencari kata "Yog" dengan case-insensitive menyesuaikan data dalam database
    re_pattern_matching = r"(?i).*"

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
        'keyword' : keyword,
        'klocation': klocation,
        'jobs_count': jobs_count,
        'categories' : categories,
        'last_n_day' : last_n_day,
        'ordering' : ordering

    }
    return context


def search_jobs(request):
    template_name = 'jobs_search/jobs_list.html'
    context = get_data(request)

    return render(request, template_name, context)


# -------------------------------------------------

def token(query_string):
  tokenize_query = word_tokenize(query_string)
  return tokenize_query
  
def stemming(query_string):
  porter = PorterStemmer()

  terms = token(query_string)
  result = []
  for term in terms:
    result.append(porter.stem(term))
  
  return result

# ----------------------api------------------------
jobs_list = ''
jobs_count = ''

@csrf_exempt
def jobs_api(request):
    
    keyword = request.POST.get('keyword')
    klocation = request.POST.get('klocation')

    date_yesterday  = request.POST.get('date_yesterday') == 'true'
    date_last_3_day  = request.POST.get('date_last_3_day') == 'true'
    date_last_14_day = request.POST.get('date_last_14_day') == 'true'
    date_last_30_day = request.POST.get('date_last_30_day') == 'true'

    cat_jobstreet = request.POST.get('cat_jobstreet') == 'true'
    cat_kalibrr   = request.POST.get('cat_kalibrr') == 'true'
    cat_glints    = request.POST.get('cat_glints') == 'true'
    
    order_relevance  = request.POST.get('order_relevance') == 'true'
    order_date       = request.POST.get('order_date') == 'true'


    global jobs_list
    global jobs_count
    
    now         = datetime.date.today()
    yesterday   = now - datetime.timedelta(days=2)
    last_3_day  = now - datetime.timedelta(days=4)
    last_14_day = now - datetime.timedelta(days=14)
    last_30_day = now - datetime.timedelta(days=30)

    
    # Searching queryset for jobs    
    '''
        filter search dapat dilakukan dengan 3 cara yang berbeda:
        Search 1 (Full text search + regex pattern (optional))
        -> Full text search merupakan fitur yang sudah disediakan oleh django untuk mempermudah searching pada keyword 
        
        jobs_list = Jobs.objects.annotate(search=SearchVector("title","company")).filter(search=r'(?i).*'+keywordTitle)
        
        Search 2 (regex search all fields)
        -> Regex search untuk all field, jika hanya ingin memfilter beberapa field tertentu atau semua
        
        entry_q = get_query(keywordTitle, ['title', 'company'])
        jobs_list = Jobs.objects.filter(entry_q)
        
        Search 3 (regex search 1 field)
        -> Regex search untuk 1 field, jika hanya ingin memfilter 1 field tertentu, atau jika ingin memfilter beberapa fields bisa menambah 
        Q untuk memfilter field yang ingin dicari. contoh: Q(field1__regex=q)|Q(field2__regex=q)...
        
        jobs_list = Jobs.objects.filter(title__regex=r'(?i).*'+keywordTitle)

    '''
    jobs_list = Jobs.objects.all() # default
    if keyword:
        q=Q()
        qs = stemming(keyword)
        for key in qs:
            q &= Q(title__iregex = r'\b{}.*\b'.format(key))|Q(company__iregex=r'\b{}.*\b'.format(key))
        # jobs_list = jobs_list.filter(q)
        
        qs = '|'.join(qs)
        jobs_list = jobs_list.filter(Q(title__iregex = r'\b.*{}.*\b'.format(qs))|Q(company__iregex=r'\b.*{}.*\b'.format(qs)))
        # jobs_list = jobs_list.filter(Q(title__icontains = keyword)|Q(company__icontains=keyword))
        jobs_count = jobs_list.count()
    if klocation:
        q=Q()
        qs = stemming(klocation)
        qs = '|'.join(qs)
        jobs_list = jobs_list.filter(location__iregex=r'\b.*{}.*\b'.format(qs))
        jobs_count = jobs_list.count()
            
    # Filter the jobs data by date
    if (order_relevance):
        jobs_list = jobs_list.annotate(rank=Case(When(reduce(operator.or_, (Q(title__iregex=key) for key in qs)),then=Value(1)), 
                                                 When(reduce(operator.or_, (Q(company__iregex=key) for key in qs)), then=Value(2)),
                                                 default=Value(99),
                                                 output_field=IntegerField())).order_by('-date_posted','rank','title')
        # jobs_list = jobs_list.order_by('rank').distinct()
    if (order_date):
        jobs_list = jobs_list.order_by('-date_posted')

    # ----------------------------------------------------------------------
    data = []

    i = 0
    for dt in jobs_list.iterator():
        data_list = model_to_dict(dt)

        # Filter the jobs data by last n days
        if (date_last_30_day and data_list['date_posted'] <= last_30_day):
            continue
        if (date_last_14_day and data_list['date_posted'] <= last_14_day):
            continue
        if (date_last_3_day and data_list['date_posted'] <= last_3_day):
            continue
        if (date_yesterday and data_list['date_posted'] <= yesterday):
            continue
        # -------------------------------------------------------------------------
        
        # Filter the jobs data by jobsite
        link = data_list['link']
        jobsite = re.sub(r"(.co.id|.com)(.*)", r"", re.sub(r"(https://www.)|(https://)", r"", link)).title()

        if (cat_jobstreet and jobsite != 'Jobstreet'):
            continue
        if (cat_kalibrr and jobsite != 'Kalibrr'):
            continue
        if (cat_glints and jobsite != 'Glints'):
            continue
        # -------------------------------------------------------------------------
        
        
        # -------------------------------------------------------------------------
        # Replace the string with re.sub (regex pattern)
        # [^MySQL|PostgreSQL|NodeJs|TypeScript|ReactJS|JavaScript|CSS|HTML|API|iOS]
        requirement = re.sub(r"([)])([A-Z])",r"\1. \n • \2", data_list['requirement'])
        requirement = re.sub(r"([a-z])([A-Z])",r"\1, \2", requirement)
        requirement = re.sub(r"([a-z]|[)])([0-9])",r"\1\n\2", requirement)
        requirement = re.sub(r"(\w+)([-]\s)",r"\1, ", requirement)
        requirement = re.sub(r"([;][-])",r", ", requirement)
        requirement = re.sub(r"(\s{2,})",r" ", requirement)
        
        requirement = re.sub(r"(react.js)",r"react js", requirement)
        requirement = re.sub(r"(MySQLTerbiasa)",r"MySQL. Terbiasa", requirement)
        requirement = re.sub(r"(, iS)",r" iOS", requirement)
        requirement = re.sub(r"(ArchitectureHave)",r"Architecture. Have", requirement)
        requirement = re.sub(r"(StoreUnderstanding)",r"Store. Understanding", requirement)
        requirement = re.sub(r"(developmentIntegration)",r"development. Integration", requirement)
        requirement = re.sub(r"(Technologyor)",r"Technology or", requirement)
        requirement = re.sub(r"(subjectProficiency)",r"subject. Proficiency", requirement)
        requirement = re.sub(r"([0-9])(Guru)",r"\1, \2 ", requirement)
        requirement = re.sub(r"(APIMampu)",r"API, Mampu", requirement)
        

        # -------------------------------------------------------------------------
        
        # Format the data jobs posted
        formatted_date = formats.date_format(data_list['date_posted'], "F, d Y")
        # -------------------------------------------------------------------------
        
        data_row = {
            'title'           : data_list['title'].title(),
            'image'           : data_list['image'],
            'company'         : data_list['company'],
            'location'        : data_list['location'],
            'requirement'     : requirement,
            'datetime_posted' : 'Posted ' + formatted_date + " by " + jobsite,
            'link'            : link,
            'detailModelId'   : 'detailModel-' + str(i),
        }
        data.append(data_row)
        i += 1 
    
    # Paginator for pagination
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
        'keyword': keyword,
        'klocation': klocation,
        'jobs': jobs
    })
    # --------------------------------------------------------------------
    
    context = {
        'data': jobs.object_list,
        'total': len(data),
        'paginator': paginate,
    }
    
    return HttpResponse(json.dumps(context, default=str), content_type="application/json")