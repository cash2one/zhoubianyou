#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-10-21 01:46:53
# Project: zuobianyou

from pyspider.libs.base_handler import *
import re
import random


class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
        }
    }

    DOMAIN = 'http://www.dianping.com/'
    LOCATIONS = ['taipei', 'hongkong']
    PROXY_POOL = ['121.12.42.91:61234', '118.114.77.47:8080', '61.135.217.7:80', '']

    @every(minutes=24 * 60)
    def on_start(self):
        # all location
        for location in self.LOCATIONS:
            self.crawl(
                'http://www.dianping.com/{location}/attraction'.format(location=location),
                callback=self.index_page,
                proxy=random.choice(self.PROXY_POOL)
            )

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        page = response.doc('div.Pages a.NextPage').items()
        if page is not None:
            self.crawl( 
                DOMAIN + page.attr.href,
                cookies=response.cookies,
                callback=self.index_page,
                proxy=random.choice(self.PROXY_POOL)
            )

        shop_selector = 'div.poi-ctn > ul > li > div.txt > div.poi-title a'
        for shop in response.doc(shop_selector).items():
            self.crawl(
                DOMAIN + shop.attr.href,
                cookies=response.cookies,
                callback=self.comment_index_page,
                proxy=random.choice(self.PROXY_POOL)
            )

    @config(priority=2)
    def comment_index_page(self, response):
        comment_list = response.doc('div#morelink-wrapper p.comment-all a')
        if comment_list is not None:
            self.crawl(
                comment_list.attr.href,
                cookies=response.cookies,
                callback=self.comment_index_page,
                proxy=random.choice(self.PROXY_POOL)
            )
        else:
            last_comment_page = response.doc('div.Pages > div.Pages a.NextPage').prevAll('a:last')
            if last_comment_page is not None:
                last_page_no = last_comment_page.attr.title
                for page_no in range(int(last_page_no)):
                    yield response.url + '?pageno={page_no}'.format({page_no=page_no})
            



