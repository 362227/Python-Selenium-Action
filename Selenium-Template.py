from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import time
import re
import requests
import os
import datetime
from datetime import datetime, timedelta

# 安装最新版的chromedriver
chromedriver_autoinstaller.install()

options = Options()
options.add_argument('--headless')
options.add_argument('--enable-javascript')
options.add_argument('blink-settings=imagesEnabled=false')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--hide-scrollbars')
options.add_argument("--headless")



with open('users.txt', 'r') as f:
    for user in f:
        user = user.strip()
        url = f'https://www.tiktok.com/@{user}'
        response = requests.get(url)
        if response.status_code == 2000:
            if '' not in response.text:
                print(f"An error occurred while scraping user {user}: page source does not contain 'videoQuality'")
                continue
        else:
            try:
                os.system('killall -9 chrome')
                driver = webdriver.Chrome(options=options)
                driver.set_page_load_timeout(15)
                driver.get(url)
                time.sleep(15)
                page_source = driver.page_source
                if '' not in page_source:
                    print(f"An error occurred while scraping user {user}: page source does not contain 'videoQuality'")
                    continue
                html=page_source
                driver.quit()
            except Exception as e:
                print(f"An exception occurred while scraping user {user}: {e}")


        # Get the current time
        now = datetime.now()

        # Only include articles from the past 100 days
        five_days_ago = now - timedelta(days=365)



        regex_link = r'scheduleTime.+?\"video\"\:\{\"id\"\:\"[0-9]{10,23}\"\,'
        regex_tit = r'contents\"\:\[\{\"desc\"\:\".*?\",'
        regex_con = r'originCover\"\:\"(.+?)\"'
        regex_pubdate = r'\"createTime\"\:\"[0-9]{7,20}\"\,\"scheduleTime'
        regex_author = r'\}\,\"author\"\:\"(.+?)\"'

        header = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss  xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
    <channel>
        <title>Tiktok @{user}</title>
        <link>https://tiktok.com</link>
        <atom:link href="https://tiktok.com" rel="self" type="application/rss+xml" />
 '''

        footer = '</channel></rss>'

        if re.findall(regex_link, html) and re.findall(regex_tit, html):
            links = re.findall(regex_link, html)
            titles = re.findall(regex_tit, html)
            articles = re.findall(regex_con, html)
            pubdates = re.findall(regex_pubdate, html)
            authors = re.findall(regex_author, html)

            # 将文章按发布时间从新到旧排序
            sorted_articles = sorted(zip(pubdates, links, titles, articles, authors), reverse=True)

            rss = ""

            # 只保留最新的30个文章
            for pubdate, link, title, article, author in sorted_articles[:30]:
                pubdate = re.sub(r'.*([0-9]{10}).*', r'\1', pubdate)
                dt = datetime.fromtimestamp(int(pubdate))
                formatted_date = dt.strftime('%a, %d %b %Y %H:%M:%S %z')
                author = re.sub(r'\}\,\"author\"\:\"(.+?)\"', r'\1', author)
                link = re.sub(r'scheduleTime.+?\"video\"\:\{\"id\"\:\"([0-9]{10,23})\"\,', r'https://www.tiktok.com/@' + author + r'/video/\1', link)
                title = re.sub(r'contents\"\:\[\{\"desc\"\:\"(.*?)\"', r'\1', title.encode('utf-8').decode('unicode_escape'))
                title = re.sub(r'contents\"\:\[\{\"desc\"\:\"|\,$', r'', title)
                article = re.sub(r'originCover\"\:\"(.+?)\"', '\1', article.encode('utf-8').decode('unicode_escape'))
                if dt >= five_days_ago:
                  rss += f'''
                <item>
                <title><![CDATA[{title}]]></title>
                <link><![CDATA[{link}]]></link>
                <description><![CDATA[<img src="{article}"  width="30%" />]]></description>
                <pubDate><![CDATA[{formatted_date}]]></pubDate>
                <author><![CDATA[{author}]]></author>
                </item>

                '''

            rss_feed = header + rss + footer

            print(rss_feed)
            with open(f'./{author}-tiktok.xml', 'w', encoding='utf-8') as f:
               f.write(rss_feed)
            with open(f'./temp/{author}-tiktok.html', 'w', encoding='utf-8') as f:
               f.write(rss_feed)

        else:
            now = datetime.now()
            formatted_date = now.strftime('%Y-%m-%d %H')
            rss_feed = f'{header}\n\t<item>\n\t\t<title>{author}出错，请检查 {formatted_date}</title>\n\t\t<link>https://www.tiktok.com/@{author}#{formatted_date}</link>\n\t</item>\n{footer}'
            print(rss_feed)
            with open(f'./{author}-tiktok.xml', 'w', encoding='utf-8') as f:
               f.write(rss_feed)
