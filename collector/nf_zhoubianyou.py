#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-10-21 01:46:53
# Project: zuobianyou

from pyspider.libs.base_handler import *
import re
import logging
import random
from collections import defaultdict

logger = logging.getLogger(__name__)


class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
        }
    }

    PROXY_UPDATER = 'proxy_updater'
    PROXY_POOL = defaultdict(int)  # proxy_host: fail_count
    FAIL_THRESHOLD = 3  # discard proxy_host after FAIL_THRESHOLD fail crawling
    COMMENT_FETCHER = 'comment_fetcher'
    LOCATIONS = [4, 7, 208, 206, 219, 345, 23, 224, 213, ]

    @every(minutes=24 * 60)
    def on_start(self):
        # all location
        for location in self.LOCATIONS:
            self.crawl(
                'http://www.dianping.com/search/category/{location}/35'.format(location=location),
                callback=self.index_page,
                proxy=random.choice(self._get_valid_proxies())
            )

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            # all location pages
            if re.match("http://www.dianping.com/search/category/\d+/35/p\d+$", each.attr.href):
                self.crawl(
                    each.attr.href,
                    cookies=response.cookies,
                    callback=self.index_page,
                    proxy=random.choice(self._get_valid_proxies())
                )
            # all shop comment first page
            if re.match("http://www.dianping.com/shop/\d+$", each.attr.href):
                # save comment detail
                self.send_message(self.COMMENT_FETCHER, {
                    'url': each.attr.href,
                    'cookies': response.cookies,
                })
                # follow
                self.crawl(
                    each.attr.href + "/review_more",
                    cookies=response.cookies,
                    callback=self.comment_index_page,
                    proxy=random.choice(self._get_valid_proxies())
                )

    @config(priority=2)
    def comment_index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            # all shop comment pages
            if re.match("http://www.dianping.com/shop/\d+/review_more\?pageno=\d+", each.attr.href):
                # save comment detail
                self.send_message(self.COMMENT_FETCHER, {
                    'url': each.attr.href,
                    'cookies': response.cookies,
                })
                # follow
                self.crawl(
                    each.attr.href,
                    cookies=response.cookies,
                    callback=self.comment_index_page,
                    proxy=random.choice(self._get_valid_proxies())
                )

    def on_message(self, project, message):
        if project == self.PROXY_UPDATER:
            # new proxy added
            proxy_host = message
            self.PROXY_POOL[proxy_host] = 0

    def _get_valid_proxies(self):
        return [
            k for k, v in filter(
                lambda k, v: v < self.FAIL_THRESHOLD, self.PROXY_POOL.iteritems()
            )
        ]
