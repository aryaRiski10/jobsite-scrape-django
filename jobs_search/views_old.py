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
from itertools import permutations

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

# ----------------------------------------------------------------------------------
def normalize_query(query_string):

    '''
    Splits the query string in invidual keywords, getting rid of unecessary spaces and grouping quoted words together.
    Example:
    >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    '''
    findterms=re.compile(r'"([^"]+)"|(\S+)').findall
    normspace=re.compile(r'\s{2,}').sub
    
    return [normspace(' ',(t[0] or t[1]).strip()) for t in findterms(query_string)]

def get_query(query_string, search_fields):

    '''
    Returns a query, that is a combination of Q objects. 
    That combination aims to search keywords within a model by testing the given search fields.
    '''

    query = None # Query to search for every search term
    terms = normalize_query(query_string)

    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__regex" % field_name: r'(?i).*'+term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
            
    return query
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


    global jobs_list
    global jobs_count
    
    now         = datetime.date.today()
    yesterday   = now - datetime.timedelta(days=1)
    last_3_day  = now - datetime.timedelta(days=4)
    last_14_day = now - datetime.timedelta(days=14)
    last_30_day = now - datetime.timedelta(days=30)

    # Searching queryset for jobs
    re_pattern_matching = r"(?i).*"
    # re_pattern_matching = r"\y{}\y"
    
    word = re.sub(r"([-])",r" ", keywordTitle)
    keyword_s = re.split(r"\s", word)
    # length = len(keyword_s)
    # out = []
    # for start in range(length):
    #     for end in range (start+1, length+1):
    #         out.append(' '.join(keyword_s[start:end]))
    #         out.append(keywordTitle)

    # perms = [' '.join(p) for p in permutations(keyword_s)]
    # if len(keyword_s) > 1:
    #     perms = [' '.join(p) for p in permutations(keyword_s,1)]
    #     query = keywordTitle+'|'+'|'.join(perms)
    # else:
    #     perms = keywordTitle
    #     query = perms
    
    query = '|'.join(keyword_s)

    print(query)

    # term_keywords = keywordTitle.split(' ')
    if keywordTitle and keywordLocation:
        # jobs_list = Jobs.objects.filter(Q(title__iregex=re_pattern_matching.format(query)) & Q(
        #     location__iregex=re_pattern_matching.format(keywordLocation)))
        # jobs_list = Jobs.objects.filter(Q(title__iregex=re_pattern_matching+keywordTitle) & Q(
        #     location__iregex=re_pattern_matching+keywordLocation))
        jobs_list = Jobs.objects.annotate(search=SearchVector("title","company")).filter(Q(search=(r"(?i).*"+keywordTitle))&Q(location__iregex=(r"(?i).*"+keywordLocation)))
        
        jobs_count = jobs_list.count()
    elif keywordTitle:
        # jobs_list = Jobs.objects.filter((Q(title__iregex=re_pattern_matching+keywordTitle)|Q(company__iregex=re_pattern_matching+keywordTitle)))
        # jobs_list = Jobs.objects.filter(Q(title__iregex=re_pattern_matching.format(query)))
        # jobs_list = Jobs.objects.annotate(search=SearchVector("title","company")).filter(search__iregex=(r"(?i).*"+keywordTitle))
        jobs_list = Jobs.objects.annotate(searchRegex=SearchVector("title","company")).filter(searchRegex=SearchQuery((r"(?i).*"+query)))

        jobs_count = jobs_list.count()
    elif keywordLocation:
        jobs_list = Jobs.objects.filter(Q(location__iregex=re_pattern_matching+keywordLocation))
        jobs_count = jobs_list.count()
    else:
        jobs_list = Jobs.objects.all()
        jobs_count = jobs_list.count()
    
    if not keywordTitle and not keywordLocation and not keywordCompany and not keywordReq:
        jobs_list = Jobs.objects.all()
        jobs_count = jobs_list.count()

    # if not keywordTitle and not keywordLocation and not keywordCompany and not keywordReq:
    #     jobs_list = Jobs.objects.all()
    #     jobs_count = jobs_list.count()
        
    # jobs_list = Jobs.objects.all() # default
    # if keywordTitle:
    #     jobs_list = jobs_list.filter(title__iregex=re_pattern.format(keywordTitle))
    #     jobs_count = jobs_list.count()
    # if keywordLocation:
    #     jobs_list = jobs_list.filter(location__iregex=re_pattern.format(keywordLocation))
    #     jobs_count = jobs_list.count()
    # if keywordCompany:
    #     jobs_list = jobs_list.filter(company__iregex=re_pattern.format(keywordCompany))
    #     jobs_count = jobs_list.count()
    # if keywordReq:
    #     jobs_list = jobs_list.filter(requirement__iregex=re_pattern.format(keywordReq))
    #     jobs_count = jobs_list.count()
    # if keyword:
    #     entry_q = get_query(keyword, ['title','company','location'])
    #     jobs_list = Jobs.objects.filter(entry_q) 
    #     jobs_count = jobs_list.count()
        
    jobs_list = jobs_list.order_by('-datetime_posted')
    # ----------------------------------------------------------------------
    
    data = []
            
    i = 0;
    for dt in jobs_list.iterator():
        data_list = model_to_dict(dt)

        # Filter the jobs data by last n days
        if (check_hari_30 and data_list['datetime_posted'] <= last_30_day):
            continue
        if (check_hari_14 and data_list['datetime_posted'] <= last_14_day):
            continue
        if (check_hari_3 and data_list['datetime_posted'] <= last_3_day):
            continue
        if (check_hari_1 and data_list['datetime_posted'] <= yesterday):
            continue
        # -------------------------------------------------------------------------
        
        # Filter the the jobs data by jobsite
        link = data_list['link']
        jobsite = re.sub(r"(.co.id|.com)(.*)", r"", re.sub(r"(https://www.)|(https://)", r"", link)).title()

        if (cat_jobstreet and jobsite != 'Jobstreet'):
            continue
        if (cat_kalibrr and jobsite != 'Kalibrr'):
            continue
        if (cat_glints and jobsite != 'Glints'):
            continue
        # -------------------------------------------------------------------------
        
        # Replace the string with re.sub (regex pattern)
        # exclude = ['MySQL','PostgreSQL','NodeJs','TypeScript','ReactJS','JavaScript','CSS','HTML','API','iOS']
        # [^MySQL|PostgreSQL|NodeJs|TypeScript|ReactJS|JavaScript|CSS|HTML|API|iOS]
        requirement = re.sub(r"([)])([A-Z])",r"\1. \n • \2", data_list['requirement'])
        # requirement = re.sub(r"([a-z])([A-Z])",r"\1, \2", requirement)
        requirement = re.sub(r"([a-z]|[)])([0-9])",r"\1\n\2", requirement)
        # requirement = re.sub(r"(\w+?[a-z])([A-Z])",r"\1\n\2", requirement)
        requirement = re.sub(r"(\w+)([-]\s)",r"\1, ", requirement)
        requirement = re.sub(r"([;][-])",r", ", requirement)
        
        requirement = re.sub(r"(react.js)",r"react js", requirement)
        requirement = re.sub(r"(MySQLTerbiasa)",r"MySQL. Terbiasa", requirement)
        requirement = re.sub(r"(, iS)",r" iOS", requirement)
        requirement = re.sub(r"(ArchitectureHave)",r"Architecture. Have", requirement)
        requirement = re.sub(r"(StoreUnderstanding)",r"Store. Understanding", requirement)
        requirement = re.sub(r"(developmentIntegration)",r"development. Integration", requirement)
        requirement = re.sub(r"(Technologyor)",r"Technology or", requirement)
        requirement = re.sub(r"(subjectProficiency)",r"subject. Proficiency", requirement)
        requirement = re.sub(r"([0-9])(Guru)",r"\1, \2 ", requirement)
        

        # -------------------------------------------------------------------------
        
        # Format the data jobs posted
        formatted_date = formats.date_format(data_list['datetime_posted'], "F, d Y")
        # -------------------------------------------------------------------------
        
        data_row = {
            'title'           : data_list['title'],
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
        'keywordTitle': keywordTitle,
        'keywordLocation': keywordLocation,
        'jobs': jobs
    })
    # --------------------------------------------------------------------
    
    context = {
        'data': jobs.object_list,
        'total': len(data),
        'paginator': paginate,
    }
    
    return HttpResponse(json.dumps(context, default=str), content_type="application/json")