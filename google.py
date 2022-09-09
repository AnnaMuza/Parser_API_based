import random
import requests
from bs4 import BeautifulSoup
from re import findall
import json

username = 'lum-customer-hl_5c45031c-zone-static-country-%s' % 'us'
password = 'kgl9t3co4494'
port = 22225
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
params = {'q': 'mens sun hat', 'client': 'firefox-b-d'}
cont = False

for i in range(20):
    try:
        session_id = random.random()
        proxy_url = ('http://%s-session-%s:%s@zproxy.lum-superproxy.io:%d' % (username, session_id, password, port))
        proxies = {'http': proxy_url, 'https': proxy_url}
        page1 = requests.get('https://httpbin.org/ip', proxies=proxies)
        print(page1.json())
        page = requests.get('https://www.google.co.in/search', params=params, headers=headers, proxies=proxies)
        print(page.status_code)
    except Exception:
        continue
    if page.status_code == 200:
        cont = True
        break

if cont:
    page = page.text
    soup = BeautifulSoup(page, 'lxml')
    s_divs = soup.findAll('div', attrs={'class': 'yuRUbf'})
    snippets = soup.findAll('span', attrs={'class': 'aCOpRe'})
    search = [{'title': s_divs[i].h3.text, 'link': s_divs[i].a['href'], 'snippet': snippets[i].text} for i in range(len(s_divs))]

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
    

    with open('page.json', 'w', encoding='utf-8') as f:
        json.dump({'search': search, 'related_questions': pairs, 'videos': videos, 'images': images}, f, ensure_ascii=False, indent=4)