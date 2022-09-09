#!/usr/local/bin/python
import json
import random
import logging
import requests
from math import ceil
from flask import Flask
from itertools import cycle
from bs4 import BeautifulSoup
from re import findall, compile
from bs4.element import Comment
from googletrans import Translator
from httpcore import SyncHTTPProxy
from requests_html import HTMLSession
from multiprocessing.pool import ThreadPool
from youtubesearchpython import SearchVideos
#from proxies import PROXIES_TRANS, PROXIES_QA
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

ALPHA_2 = {'au': 'amazon.com.au', 'br': 'amazon.com.br', 'ca': 'amazon.ca', 'cn': 'amazon.cn',\
           'fr': ['amazon.fr', 'session-id=257-0076351-7670068; ubid-acbfr=257-8917983-1333849'],\
           'de': ['amazon.de', 'session-id=262-1749175-4288611; ubid-acbde=258-8870827-8574318'],\
           'in': 'amazon.in',\
           'it': ['amazon.it', 'session-id=262-8621499-2659916; ubid-acbit=261-2634399-5300121'],\
           'jp': 'amazon.co.jp', 'mx': 'amazon.com.mx', 'nl': 'amazon.nl', 'sa': 'amazon.sa', 'sg': 'amazon.sg', 'es': 'amazon.es',\
           'tr': 'amazon.com.tr', 'ae': 'amazon.ae', 'gb': 'amazon.co.uk',\
           'us': ['amazon.com', 'session-id=138-9277706-8236251; ubid-main=132-3784405-2244251']}


class GT:
    def __init__(self):
        while True:
            self.translator = Translator(service_urls=['translate.google.com'])
            try:
                self.translator.detect('Hello there')
                break
            except Exception:
                continue


class Translate(Resource, GT):
    def post(self):
        def translate(text):
            
            # username = 'lum-customer-hl_5c45031c-zone-static'
            # password = 'kgl9t3co4494'
            # port = 22225
            # session_id = random.random()
            # proxy_url = ('http://%s-session-%s:%s@zproxy.lum-superproxy.io:%d' % (username, session_id, password, port))

            if self.data['from']:
                obj = self.translator.translate(text, src=self.data['from'], dest=self.data['to'])
            else:
                obj = self.translator.translate(text, dest=self.data['to'])
            return obj.text

        parser = reqparse.RequestParser()
        parser.add_argument("text")
        parser.add_argument("from")
        parser.add_argument("to")
        self.data = parser.parse_args()
        self.text = self.data['text']

        for _ in range(5):
            try:
                pool = ThreadPool(10)
                res = pool.map(translate, [self.text[5000*i:5000*(i+1)] for i in range(0, ceil(len(self.text)/5000))])
                output = ''.join(res)

                return {"error": 'false', "text": output}, 200
            except Exception:
                continue
        return {"error": 'true', "text": ""}, 200


class YouTube(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("search")
        parser.add_argument("videos")
        data = parser.parse_args()
        num = int(data['videos']) if int(data['videos']) else 5
        search = SearchVideos(data['search'], offset=1, mode="json", max_results=num).result()

        return json.loads(search), 200


class Images(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("search")
        parser.add_argument("images")
        data = parser.parse_args()
        num = int(data['images']) if int(data['images']) else 5
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
        params = {'q': data['search'], 'source': 'lnms', 'tbm': 'isch'}

        with HTMLSession() as session:
            page = session.get('https://www.google.co.in/search', params=params, headers=headers).text

        extensions = ("jpg", "jpeg", "png", "gif")
        html = page.split('["')
        urls = []

        for i in html:
            if i.startswith('http') and i.split('"')[0].split('.')[-1] in extensions:
                urls.append(i.split('"')[0])
            if len(urls) == num:
                break

        return {'images_urls': urls}, 200


class Google(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("search")
        data = parser.parse_args()
        username = 'lum-customer-hl_5c45031c-zone-static'
        password = 'kgl9t3co4494'
        port = 22225
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
        params = {'q': data['search'], 'client': 'firefox-b-d'}
        cont = False

        for i in range(20):
            try:
                session_id = random.random()
                proxy_url = ('http://%s-session-%s:%s@zproxy.lum-superproxy.io:%d' % (username, session_id, password, port))
                proxies = {'http': proxy_url, 'https': proxy_url}
                # page1 = requests.get('https://httpbin.org/ip', proxies=proxies)
                # print(page1.json())
                page = requests.get('https://www.google.co.in/search', params=params, headers=headers, proxies=proxies)
                # print(page.status_code)
            except Exception:
                continue
            if page.status_code == 200:
                cont = True
                break

        if cont:
            page = page.text
            soup = BeautifulSoup(page, 'lxml')
            s_divs = soup.findAll('div', attrs={'class': 'yuRUbf'})
            search = [{'title': i.h3.text, 'link': i.a['href']} for i in s_divs]

            code = page.split('// Google Inc.')[1].split('try{')[0]
            code = code.encode('utf8').decode('unicode_escape')
            soup_code = BeautifulSoup(code, 'lxml')
            q_divs = soup_code.findAll('div', attrs={'class': 'iOBnre match-mod-horizontal-padding'})
            questions = [i.a.text for i in q_divs]
            a_divs = soup_code.findAll('div', attrs={'class': 'mod'})
            answers = list(filter(lambda x: len(x['class']) == 1, a_divs))
            pairs = [{'question': questions[i], 'answer': str(answers[i])} for i in range(len(questions))]

            try:
                v_divs = soup.findAll('div', attrs={'class': 'VibNM'})
                v_div = v_divs[0].parent
                videos1 = [i.a['href'] for i in v_divs]
                t_divs = v_div.findAll('div', attrs={'role': 'heading'})
                titles = [i.text for i in t_divs]
                videos = [{'title': titles[i], 'video': videos1[i]} for i in range(len(titles))]
            except (AttributeError, IndexError):
                videos = []

            try:
                i_div = soup.find('div', attrs={'jscontroller': 'IkchZc'})
                i_img = i_div.findAll('img')
                images = [i['title'] for i in i_img]
            except AttributeError:
                images = []

            return {'error': 'false', 'search': search, 'related_questions': pairs, 'videos': videos, 'images': images}, 200
        else:
            return {'error': 'true', 'search': [], 'related_questions': [], 'videos': [], 'images': []}, 200


class Amazon(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("search")
        parser.add_argument("country")
        data = parser.parse_args()
        data['country'] = 'us' if not data['country'] else data['country']

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0', 'Cookie': ALPHA_2[data['country']][1]}
        page = requests.get('https://www.{}/s'.format(ALPHA_2[data['country']][0]), params={'k': data['search']}, headers=headers).text
        soup = BeautifulSoup(page, 'lxml')
        toolbar = soup.find('h1', attrs={'class': 'a-size-base s-desktop-toolbar a-text-normal'})
        try:
            results_text = toolbar.find('span', attrs={'dir': 'auto'})
            results = findall(r'\d[0-9.,\-\s]+\d', results_text.text)[1]
        except (AttributeError, IndexError):
            return {'all_results': 0, 'products': [], 'related_searches': []}, 200

        main_block = soup.find('div', attrs={'class': 's-main-slot s-result-list s-search-results sg-row'})
        prods = main_block.findAll('div', attrs={'data-asin': compile(r'\w{10}')})
        products = []
    
        for i in prods:
            d = {}
            name = i.find('span', attrs={'class': 'a-size-medium a-color-base a-text-normal'})
            if not name:
                name = i.find('span', attrs={'class': 'a-size-base-plus a-color-base a-text-normal'})
            ad = 'AdHolder' in ' '.join(i['class'])

            if name and not ad:
                d.update({'name': name.text})
                img = i.find('img', attrs={'class': 's-image'})
                d.update({'image': img['src']})

                price = i.findAll('span', attrs={'class': 'a-offscreen'})
                try:
                    if len(price) == 2:
                        d.update({'price': findall(r'\d[0-9,.\s]+\d', price[1].text)[0]})
                        d.update({'price_discount': findall(r'\d[0-9,.\s]+\d', price[0].text)[0]})
                    else:
                        d.update({'price': findall(r'\d[0-9,.\s]+\d', price[0].text)[0]})
                        d.update({'price_discount': 0})

                except IndexError:
                    d.update({'price': 0})
                    d.update({'price_discount': 0})

                rat = i.find('span', attrs={'class': 'a-icon-alt'})
                try:
                    d.update({'rating': rat.text[0:3]})
                except AttributeError:
                    d.update({'rating': 0})

                com = i.find('span', attrs={'class': 'a-size-base', 'dir': 'auto'})
                try:
                    d.update({'comments': com.text})
                except AttributeError:
                    d.update({'comments': 0})

                d.update({'ASIN': i['data-asin']})
                products.append(d)

        rel_block = soup.find('span', attrs={'data-component-props': '{"name":"loom-desktop-bottom-slot_rsps-related-searches"}'})

        try:
            rel_block = rel_block.find('ol', attrs={'class': 'a-carousel', 'role': 'list'})
            rel_block_list = rel_block.findAll('li')
            relared_searches = []

            for i in rel_block_list:
                d = {}
                name = i.find('a', attrs={'class': 'a-size-base-plus a-link-normal'})
                d.update({'name': name.text.strip()})
                img = i.findAll('img')
                d.update({'image': img[1]['src']})
                relared_searches.append(d)
            return {'all_results': results, 'products': products, 'related_searches': relared_searches}, 200

        except AttributeError:
            return {'all_results': results, 'products': products, 'related_searches': []}, 200


class AmazonASIN(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("asin")
        parser.add_argument("country")
        data = parser.parse_args()
        data['country'] = 'us' if not data['country'] else data['country']
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0', 'Cookie': ALPHA_2[data['country']][1]}
        page = requests.get('https://www.{}/dp/{}'.format(ALPHA_2[data['country']][0], data['asin']), headers=headers).text
        soup = BeautifulSoup(page, 'lxml')
        try:
            title = soup.find('span', attrs={'id': 'productTitle'}).text.strip()
        except AttributeError:
            return {'title': '', 'images': [], 'bullets': [], 'description': '', 'Q&A': [], 'reviews': []}

        scripts = soup.findAll('script', attrs={'type': 'text/javascript'})
        for i in scripts:
            i = str(i)
            if 'P.when(\'A\').register("ImageBlockATF", function(A){' in i:
                s = json.loads(findall(r'\[{"hiRes":".+}\]', i)[0])
        images = [i['hiRes'] for i in s]

        try:
            bul_div = soup.find('div', attrs={'id': 'feature-bullets'})
            bul_list = bul_div.findAll('li')
            try:
                bul_list = bul_list[1:] if 'aok-hidden' in bul_list[0]['class'][0] else bul_list
            except KeyError:
                pass
            bullets = [i.text.strip() for i in bul_list]
        except IndexError:
            bullets = []

        try:
            description = soup.find('div', attrs={'id': 'productDescription'}).p.text.strip()
        except AttributeError:
            description = ''

        try:
            qa_href = soup.find('div', attrs={'class': 'cdQuestionLazySeeAll'}).a['href']
            qa_page = requests.get(qa_href, headers=headers).text
            qa_soup = BeautifulSoup(qa_page, 'lxml')
            qa_div = qa_soup.find('div', attrs={'class': 'a-section askTeaserQuestions'})
            qa_divs = qa_div.findChildren('div', recursive=False)
            qa = []
            for i in qa_divs:
                try:
                    s = i.findAll('span')
                    q = s[6].text.strip()
                    a = s[8].text.strip()
                    qa.append({'question': q, 'answer': a})
                except IndexError:
                    pass
        except AttributeError:
            qa = []

        rev_divs = soup.findAll('div', attrs={'data-hook': 'review-collapsed'})
        reviews = [i.getText().strip() for i in rev_divs]

        return {'title': title, 'images': images, 'bullets': bullets, 'description': description, 'Q&A': qa, 'reviews': reviews}


api.add_resource(Translate, "/translate", "/translate/", "/translate/<int:id>")
api.add_resource(YouTube, "/youtube", "/youtube/", "/youtube/<int:id>")
api.add_resource(Images, "/images", "/images/", "/images/<int:id>")
api.add_resource(Google, "/google", "/google/", "/google/<int:id>")
api.add_resource(Amazon, "/amazon", "/amazon/", "/amazon/<int:id>")
api.add_resource(AmazonASIN, "/amazon_asin", "/amazon_asin/", "/amazon_asin/<int:id>")

if __name__ == '__main__':
    app.run(host='0.0.0.0', use_reloader=False, processes=1)