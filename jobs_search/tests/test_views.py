from django.test import TestCase, Client
from django.urls import reverse
from jobs_search.models import Jobs

class TestViews(TestCase):
    
    def test_get_data_GET(self):
        client = Client()
        
        response = client.get(reverse('jobs_search'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs_search/jobs_list.html')