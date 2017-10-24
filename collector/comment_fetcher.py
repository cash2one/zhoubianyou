#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-10-21 01:46:53
# Project: zuobianyou

from pyspider.libs.base_handler import *
import logging
import json
import random
from datetime import datetime
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

    def on_start(self):
        # crawl dummy page for running io_loop
        self.crawl('http://www.baidu.com', auto_recrawl=True, age=10, callback=self.dummy_page)

    def dummy_page(self, response):
        return {'date': datetime.now()}

    def comment_detail_page(self, response):
        logger.info(response.headers)
        # TODO: traverse all comments and images, then save
        shop_selector = '#top > div.shop-wrap.shop-revitew > div.aside > div > div.info-name > h2 > a'
        shop_item = response.doc(shop_selector)
        shop_name = shop_item.text()
        try:
            shop_id = response.url.split('/')[2]
        except ValueError:
            shop_id = None
        comments_block_selector = '#top > div.shop-wrap.shop-revitew > div.main > div > div.comment-mode > div.comment-list > ul > li'
        for comment_item in response.doc(comments_block_selector).items():
            user_name_selector = 'div.pic > p.name > a'
            user_name = comment_item(user_name_selector).text()
            user_rate_selector = 'div.content > div.user-info > span'
            user_rate = comment_item(user_rate_selector).attr.title
            comment_txt_selector = 'div.content > div.comment-txt > div'
            comment_txt = comment_item(comment_txt_selector).text()
            create_time_selector = 'div.misc-info > span.time'
            create_time = comment_item(create_time_selector).text()
            comment = {
                'shop_id': shop_id,
                'shop_name': shop_name,
                'user_name': user_name,
                'user_rate': user_rate,
                'comment_txt': comment_txt,
                'create_time': create_time,
            }
            self.send_message(self.project_name, comment, md5string(json.dumps(comment)))

    def on_message(self, project, message):
        if project == self.PROXY_UPDATER:
            # new proxy added
            proxy_host = message
            self.PROXY_POOL[proxy_host] = 0
        elif project == self.project_name:
            # save one comment record
            return message
        else:
            # should be index fetcher
            url = message.get('url')
            cookies = message.get('cookies')
            assert(url)
            self.crawl(
                url,
                cookies=cookies,
                proxy=random.choice(self._get_valid_proxies()),
                callback=self.comment_detail_page,
            )

    def _get_valid_proxies(self):
        proxies = [
            k for k, v in filter(
                lambda item: item[1] < self.FAIL_THRESHOLD, self.PROXY_POOL.iteritems()
            )
        ]
        return proxies if proxies else ['']
