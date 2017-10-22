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

    LOCATIONS = ['taipei', 'hongkong']
    PROXY_POOL = ['121.31.101.118:8123', '121.31.100.53:8123', '110.72.38.227:8123', '117.78.37.198:8000']

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
        page = response.doc('div.Pages a.NextPage')
        if page is not None:
            self.crawl(
                page.attr.href,
                cookies=response.cookies,
                callback=self.index_page,
                proxy=random.choice(self.PROXY_POOL)
            )

        shop_selector = 'div.poi-ctn > ul > li > div.txt > div.poi-title a'
        for shop in response.doc(shop_selector).items():
            self.crawl(
                shop.attr.href,
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
                callback=self.comment_list_page,
                proxy=random.choice(self.PROXY_POOL)
            )
    
    @config(priority=3)
    def comment_list_page(self, response):
        last_comment_page = response.doc('div.Pages > div.Pages a.NextPage')
        yield {'url' : last_comment_page.attr.href}
        if last_comment_page is not None:
            last_page_no = last_comment_page.attr.title
            
            # for page_no in range(int(last_page_no)):
              #  yield {'url' : response.url + '?pageno={page_no}'.format(page_no=page_no)}
