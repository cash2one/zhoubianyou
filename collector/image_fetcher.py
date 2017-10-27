#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-10-21 01:46:53
# Project: image_fetcher

from pyspider.libs.base_handler import *
import logging
import random
import os
from collections import defaultdict

logger = logging.getLogger(__name__)


class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
        }
    }
    # TODO: 是否需要分层文件结构存储,防止单一目录文件数量过多
    BASE_DIR_PATH = '/code/data/images/'
    PROXY_UPDATER = 'update_proxy'
    PROXY_POOL = defaultdict(int)  # proxy_host: fail_count
    FAIL_THRESHOLD = 3  # discard proxy_host after FAIL_THRESHOLD fail crawling

    def on_start(self):
        if not os.path.isdir(self.BASE_DIR_PATH):
            os.makedirs(self.BASE_DIR_PATH)
        # test image fetcher
        url = 'http://qcloud.dpfile.com/pc/WwVccGSGdJk32ZbslqciG2dQN0mzg5ezN2b0gRTKGz65m9ai5Dwcre_SlpgUg8LoF5u7J_jS4MuCaeLAHD0KTg.jpg'
        self.crawl(
            url,
            auto_recrawl=True,
            age=500,
            callback=self.image_detail_page,
            save={'ext': 'jpg', 'filename': 'testimage'}
        )

    @catch_status_code_error
    def image_detail_page(self, response):
        if not response.ok:
            cookies = None
            if response.save:
                old_proxy = response.save.get('proxy')
                # mark old proxy failed
                if old_proxy:
                    self.PROXY_POOL[old_proxy] += 1
                cookies = response.save.get('cookies')
            # recrawl with another proxy
            current_proxy = random.choice(self._get_valid_proxies())
            ext = response.save['ext']
            file_name = response.save['filename']
            self.crawl(
                response.url,
                cookies=cookies,
                proxy=current_proxy,
                callback=self.image_detail_page,
                retries=0,  # 关闭retry
                connect_timeout=5,
                save={
                    'ext': ext,
                    'filename': file_name,
                    'cookies': cookies,
                    'proxy': current_proxy
                }
            )
        else:
            ext = response.save['ext']
            file_name = response.save['filename']
            file_path = os.path.join(self.BASE_DIR_PATH, file_name + '.' + ext)
            content = response.content
            self.save_img(content, file_path)

    def on_message(self, project, message):
        if project == self.PROXY_UPDATER:
            # new proxy added
            proxy_host = message
            if not self.PROXY_POOL.get(proxy_host):
                self.PROXY_POOL[proxy_host] = 0
        else:
            # should be index fetcher
            url = message.get('url')
            cookies = message.get('cookies')
            ext = message.get('ext')
            file_name = message.get('filename')
            current_proxy = random.choice(self._get_valid_proxies())
            self.crawl(
                url,
                cookies=cookies,
                proxy=current_proxy,
                callback=self.image_detail_page,
                retries=0,  # 关闭retry
                connect_timeout=5,  # 缩短连接探测时间
                save={
                    'ext': ext,
                    'filename': file_name,
                    'cookies': cookies,
                    'proxy': current_proxy
                }
            )

    def _get_valid_proxies(self):
        proxies = [
            k for k, v in filter(
                lambda item: item[1] < self.FAIL_THRESHOLD, self.PROXY_POOL.iteritems()
            )
        ]
        return proxies if proxies else ['']

    def save_img(self, content, path):
        with open(path, "wb+") as f:
            f.write(content)
