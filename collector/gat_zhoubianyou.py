#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-10-21 01:46:53
# Project: gat_zhoubianyou

from pyspider.libs.base_handler import *
import re
import random
from collections import defaultdict


class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
        }
    }
    PROXY_UPADATER = 'proxy_updater'
    PROXY_POOL = defaultdict(int)#['121.31.101.118:8123', '121.31.100.53:8123', '110.72.38.227:8123', '117.78.37.198:8000']
    FAIL_THRESHOLD = 3
    COMMENT_FETCHER = 'comment_fetcher'
    LOCATIONS = ['taipei', 'hongkong']

    @every(minutes=24 * 60)
    def on_start(self):
        # all location
        for location in self.LOCATIONS:
            proxy = random.choice(self._get_valid_proxies())
            self.crawl(
             'http://www.dianping.com/{location}/attraction'.format(location=location),
                callback=self.index_page,
                proxy=proxy,
                save={'proxy': proxy}
            )

    @config(age=24 * 60 * 60)
    @catch_status_code_error
    def index_page(self, response):
        proxy = response.save.get('proxy')
        if not response.ok:
            self.PROXY_POOL[proxy] += 1
            return
        page = response.doc('div.Pages a.NextPage')
        if page is not None:
            proxy = random.choice(self._get_valid_proxies())
            self.crawl(
                page.attr.href,
                cookies=response.cookies,
                callback=self.index_page,
                proxy=proxy,
                save={'proxy': proxy}
            )

        shop_selector = 'div.poi-ctn > ul > li > div.txt > div.poi-title a'
        for shop in response.doc(shop_selector).items():
            proxy = random.choice(self._get_valid_proxies())
            self.crawl(
                shop.attr.href + '/review_more',
                cookies=response.cookies,
                callback=self.comment_index_page,
                proxy=proxy,
                save={'proxy':proxy}
            )

    @config(priority=2, age=24*60*60)
    @catch_status_code_error
    def comment_index_page(self, response):
        proxy = response.save.get('proxy')
        if not response.ok:
            self.PROXY_POOL[proxy] += 1
            return
        for each in response.doc('a[href^="http"]').items():
            # all shop comment pages
            if re.match("http://www.dianping.com/shop/\d+/review_more\?pageno=\d+", each.attr.href):
                # save comment detail
                self.send_message(self.COMMENT_FETCHER, {
                    'url': each.attr.href,
                    'cookies': response.cookies,
                })
                # follow
                proxy = random.choice(self._get_valid_proxies())
                self.crawl(
                    each.attr.href,
                    cookies=response.cookies,
                    callback=self.comment_index_page,
                    proxy=proxy,
                    save={'proxy': proxy}
                )

    def on_message(self, project, message):
        if project == self.PROXY_UPDATER:
            # new proxy added
            proxy_host = message
            self.PROXY_POOL[proxy_host] = 0

    def _get_valid_proxies(self):
        # TODO: GC proxy pool
        proxies = [
            (k,v) for k, v in filter(
                lambda k, v: v <= self.FAIL_THRESHOLD, self.PROXY_POOL.iteritems()
            )
        ]
        return proxies if proxies else ['']
