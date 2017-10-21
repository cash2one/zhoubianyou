#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-10-21 01:46:53
# Project: zuobianyou

from pyspider.libs.base_handler import *
import re
import logging
import random

logger = logging.getLogger(__name__)


class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
        }
    }

    LOCATIONS = [4, 7, 208, 206, 219, 345, 23, 224, 213, ]
    PROXY_POOL = ['121.12.42.91:61234', '118.114.77.47:8080', '61.135.217.7:80', '']

    @every(minutes=24 * 60)
    def on_start(self):
        # all location
        for location in self.LOCATIONS:
            self.crawl(
                'http://www.dianping.com/search/category/{location}/35'.format(location=location),
                callback=self.index_page,
                proxy=random.choice(self.PROXY_POOL)
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
                    proxy=random.choice(self.PROXY_POOL)
                )
            # all shop comment first page
            if re.match("http://www.dianping.com/shop/\d+$", each.attr.href):
                # save comment detail
                self.crawl(
                    each.attr.href,
                    cookies=response.cookies,
                    callback=self.comment_detail_page,
                    proxy=random.choice(self.PROXY_POOL)
                )
                # follow
                self.crawl(
                    each.attr.href + "/review_more",
                    cookies=response.cookies,
                    callback=self.comment_index_page,
                    proxy=random.choice(self.PROXY_POOL)
                )

    @config(priority=2)
    def comment_index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            # all shop comment pages
            if re.match("http://www.dianping.com/shop/\d+/review_more\?pageno=\d+", each.attr.href):
                # save comment detail
                self.crawl(each.attr.href,
                    cookies=response.cookies,
                    callback=self.comment_detail_page,
                    proxy=random.choice(self.PROXY_POOL)
                )
                # follow
                self.crawl(each.attr.href,
                    cookies=response.cookies,
                    callback=self.comment_index_page,
                    proxy=random.choice(self.PROXY_POOL)
                )

    @config(priority=3)
    def comment_detail_page(self, response):
        logger.info(response.headers)
        # TODO: traverse all comments and images, then save
        place_selector = '#top > div.shop-wrap.shop-revitew > div.aside > div > div.info-name > h2 > a'
        place_name = response.doc(place_selector).text()
        comments_block_selector = '#top > div.shop-wrap.shop-revitew > div.main > div > div.comment-mode > div.comment-list > ul > li'
        comments = []
        for comment_item in response.doc(comments_block_selector).items():
            user_name_selector = 'div.pic > p.name > a'
            user_name = comment_item(user_name_selector).text()
            user_rate_selector = 'div.content > div.user-info > span'
            user_rate = comment_item(user_rate_selector).attr.title
            comment_txt_selector = 'div.content > div.comment-txt > div'
            comment_txt = comment_item(comment_txt_selector).text()
            comment = {
                'place_name': place_name,
                'user_name': user_name,
                'user_rate': user_rate,
                'comment_txt': comment_txt,
            }
            comments.append(comment)
        return comments
