import requests
import re
import os
from bs4 import BeautifulSoup

def ptt(target, pic_c):
    my_headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
    payload = {"from": "/bbs/Gossiping/M.1725445765.A.E50.html", "yes": "yes"}
    session = requests.session()
    session.post("https://www.ptt.cc/ask/over18", payload)
    url = "https://www.ptt.cc"
    url_head = url + "/bbs/Beauty/index.html"
    n, count = 10, 0
    os.makedirs(target,exist_ok=True)
    while True:
        r = session.get(url_head, headers=my_headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text.split("r-list-sep")[0], 'html.parser')
            title = soup.select('div.title')
            link = soup.select('div.title a')
            date = soup.select('div.date')
            url_head = url + soup.select('a.btn.wide')[1].get('href')
            for i, j, d in zip(title[::-1], link[::-1], date[::-1]):
                if "Re:" in i.text or "刪除)" in i.text:
                    continue
                if target not in i.text.strip(): continue
                try:
                    r2 = session.get(url + j.get('href'), headers=my_headers)
                    soup2 = BeautifulSoup(r2.text, 'html.parser')
                    cut = soup2.select('span.article-meta-value')[3]
                    soup3 = BeautifulSoup(r2.text.split(str(cut))[1].split('<span class="f2')[0], 'html.parser')
                    for p in soup3.find_all('a'):
                        if pic_c == count:
                            print("抓取完畢")
                            return
                        picurl = p.get('href')
                        name = picurl[picurl.rfind("/")+1:]
                        pic_r = session.get(picurl, headers=my_headers)
                        if pic_r.status_code == 200:
                            if re.search(r"\.(jpg|jpeg|gif|png)$", picurl):
                                with open(target+"/"+name,"wb") as fw:
                                    for fp in pic_r:
                                        fw.write(fp)
                                    count += 1
                except requests.exceptions.HTTPError:
                    pass
while True:
    kind = input("請輸入所需圖片(q結束):")
    if kind == "q" or kind == "Q":
        print("程式結束")
        break
    else:
        quantity = eval(input("請輸入搜尋多少張:"))
        print("請耐心等待---")
        ptt(kind, quantity)
