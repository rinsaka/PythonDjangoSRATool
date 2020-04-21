from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from .models import UploadFile

# Create your tests here.


class SraIndexTests(TestCase):
    def test_sra_index(self):
        """ Sra index のテスト """
        response = self.client.get(reverse('sras:index'))
        self.assertEqual(response.status_code, 200)


class SraDMALT_DS3Tests(TestCase):
    def test_sra_upload(self):
        """ DS3のテスト """
        uploadfile = UploadFile.objects.create(
            id="01E468VB1ZEP4MGJTNCH1P4CX4",
            name="3-DS-R3.csv",
            file="0003-ds-r3.csv",
            created_at=timezone.now(),
            updated_at=timezone.now())
        url = reverse('sras:show', args=(uploadfile.id,))
        response = self.client.get(url)
        self.assertContains(response, "3-DS-R3")

        url = reverse('sras:table', args=(uploadfile.id,))
        response = self.client.get(url)
        self.assertContains(response, "3-DS-R3")

        url = reverse('sras:chart', args=(uploadfile.id,))
        response = self.client.get(url)
        self.assertContains(response, "Defects found")

        # Analyst のテスト（DMALTモデル）
        # exp
        c = Client()
        data = {

            'srmodel':'dmalt_exp',
            'n_metrics':'2',
            'max_tData':'12',
            'max_tPrediction':'14',
            'init_a':'61',
            'init_b':'0.01',
            'str_tData':'0,1,2,3,4,5,6,7,8,9,10,11,12',
            'str_yData':'0,6,9,13,20,28,40,48,54,57,59,60,61',
            'str_tPrediction':'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14',
            'acumulation_met1':'on',
            'init_met1':'0.001',
            'acumulation_met2':'on',
            'init_met2':'0.001',
        }
        c.post('/01E468VB1ZEP4MGJTNCH1P4CX4/analyst/', data)

        # earlang
        c = Client()
        data = {
            'srmodel': 'dmalt_earlang',
            'n_metrics':'2',
            'max_tData':'12',
            'max_tPrediction':'14',
            'init_a':'61',
            'init_b':'0.01',
            'str_tData':'0,1,2,3,4,5,6,7,8,9,10,11,12',
            'str_yData':'0,6,9,13,20,28,40,48,54,57,59,60,61',
            'str_tPrediction':'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14',
            'acumulation_met1': 'on',
            'init_met1': '0.0001',
            'acumulation_met2': 'on',
            'init_met2': '0.0001',
        }
        c.post('/01E468VB1ZEP4MGJTNCH1P4CX4/analyst/', data)

        # ray
        c = Client()
        data = {
            'srmodel': 'dmalt_ray',
            'n_metrics':'2',
            'max_tData':'12',
            'max_tPrediction':'14',
            'init_a':'61',
            'init_b':'10',
            'str_tData':'0,1,2,3,4,5,6,7,8,9,10,11,12',
            'str_yData':'0,6,9,13,20,28,40,48,54,57,59,60,61',
            'str_tPrediction':'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14',
            'acumulation_met1': 'on',
            'init_met1': '0.0001',
            'acumulation_met2': 'on',
            'init_met2': '0.0001',
        }
        c.post('/01E468VB1ZEP4MGJTNCH1P4CX4/analyst/', data)

        # gamma
        c = Client()
        data = {
            'srmodel': 'dmalt_gamma',
            'n_metrics':'2',
            'max_tData':'12',
            'max_tPrediction':'14',
            'init_a':'61',
            'init_b':'0.01',
            'init_c': '1',
            'str_tData':'0,1,2,3,4,5,6,7,8,9,10,11,12',
            'str_yData':'0,6,9,13,20,28,40,48,54,57,59,60,61',
            'str_tPrediction':'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14',
            'acumulation_met1': 'on',
            'init_met1': '0.0001',
            'acumulation_met2': 'on',
            'init_met2': '0.0001',
        }
        c.post('/01E468VB1ZEP4MGJTNCH1P4CX4/analyst/', data)

        # weibull
        c = Client()
        data = {
            'srmodel': 'dmalt_wei',
            'n_metrics':'2',
            'max_tData':'12',
            'max_tPrediction':'14',
            'init_a':'61',
            'init_b':'0.01',
            'init_c': '1',
            'str_tData':'0,1,2,3,4,5,6,7,8,9,10,11,12',
            'str_yData':'0,6,9,13,20,28,40,48,54,57,59,60,61',
            'str_tPrediction':'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14',
            'acumulation_met1': 'on',
            'init_met1': '0.0001',
            'acumulation_met2': 'on',
            'init_met2': '0.0001',
        }
        c.post('/01E468VB1ZEP4MGJTNCH1P4CX4/analyst/', data)


class SraNHPP_DS3Tests(TestCase):
    def test_sra_upload(self):
        """ DS3のテスト """
        uploadfile = UploadFile.objects.create(
            id="01E468VKF98EKFKJCNPCMPVS4X",
            name="3-DS-R3.csv",
            file="0003-ds-r3.csv",
            created_at=timezone.now(),
            updated_at=timezone.now())
        url = reverse('sras:show', args=(uploadfile.id,))
        response = self.client.get(url)
        self.assertContains(response, "3-DS-R3")

        url = reverse('sras:table', args=(uploadfile.id,))
        response = self.client.get(url)
        self.assertContains(response, "3-DS-R3")

        url = reverse('sras:chart', args=(uploadfile.id,))
        response = self.client.get(url)
        self.assertContains(response, "Defects found")

        # Analyst のテスト（NHPPモデル）
        # exp
        c = Client()
        data = {
            'srmodel':'nhpp_exp',
            'n_metrics':'2',
            'max_tData':'12',
            'max_tPrediction':'14',
            'init_a':'61',
            'init_b':'0.01',
            'str_tData':'0,1,2,3,4,5,6,7,8,9,10,11,12',
            'str_yData':'0,6,9,13,20,28,40,48,54,57,59,60,61',
            'str_tPrediction':'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14',
        }
        c.post('/01E468VKF98EKFKJCNPCMPVS4X/analyst/', data)

        # earlang
        c = Client()
        data = {
            'srmodel':'nhpp_earlang',
            'n_metrics':'2',
            'max_tData':'12',
            'max_tPrediction':'14',
            'init_a':'61',
            'init_b':'0.01',
            'str_tData':'0,1,2,3,4,5,6,7,8,9,10,11,12',
            'str_yData':'0,6,9,13,20,28,40,48,54,57,59,60,61',
            'str_tPrediction':'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14',
        }
        c.post('/01E468VKF98EKFKJCNPCMPVS4X/analyst/', data)

        # ray
        c = Client()
        data = {
            'srmodel':'nhpp_ray',
            'n_metrics':'2',
            'max_tData':'12',
            'max_tPrediction':'14',
            'init_a':'61',
            'init_b':'10',
            'str_tData':'0,1,2,3,4,5,6,7,8,9,10,11,12',
            'str_yData':'0,6,9,13,20,28,40,48,54,57,59,60,61',
            'str_tPrediction':'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14',
        }
        c.post('/01E468VKF98EKFKJCNPCMPVS4X/analyst/', data)

        # gamma
        c = Client()
        data = {
            'srmodel':'nhpp_gamma',
            'n_metrics':'2',
            'max_tData':'12',
            'max_tPrediction':'14',
            'init_a':'61',
            'init_b':'0.1',
            'str_tData':'0,1,2,3,4,5,6,7,8,9,10,11,12',
            'str_yData':'0,6,9,13,20,28,40,48,54,57,59,60,61',
            'str_tPrediction':'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14',
        }
        c.post('/01E468VKF98EKFKJCNPCMPVS4X/analyst/', data)

        # weibull
        c = Client()
        data = {
            'srmodel':'nhpp_wei',
            'n_metrics':'2',
            'max_tData':'12',
            'max_tPrediction':'14',
            'init_a':'61',
            'init_b':'0.01',
            'str_tData':'0,1,2,3,4,5,6,7,8,9,10,11,12',
            'str_yData':'0,6,9,13,20,28,40,48,54,57,59,60,61',
            'str_tPrediction':'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14',
        }
        c.post('/01E468VKF98EKFKJCNPCMPVS4X/analyst/', data)

        #
        ###  except ValueError: をカバーできるが，エラーも表示されるので微妙
        ###
        ###
        # c = Client()
        # data = {
        #     'n_metrics':'2',
        #     'max_t':'12',
        #     'srmodel':'nhpp_wei',
        #     'init_a':'61',
        #     'init_b':'0.00001',
        #     'init_c':'100',
        #     'max_x':'12',
        # }
        # c.post('/01E468VKF98EKFKJCNPCMPVS4X/analyst/', data)

class SraUploadTests(TestCase):
    def test_show_upload_form(self):
        """ Sra Upload のテスト """
        response = self.client.get(reverse('sras:upload'))
        self.assertEqual(response.status_code, 200)
