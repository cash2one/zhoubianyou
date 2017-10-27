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
    DIR_PATH = '/tmp/image/'
    PROXY_UPDATER = 'proxy_updater'
    PROXY_POOL = defaultdict(int)  # proxy_host: fail_count
    FAIL_THRESHOLD = 3  # discard proxy_host after FAIL_THRESHOLD fail crawling

    def on_start(self):
        # test image fetcher
        url = 'http://qcloud.dpfile.com/pc/WwVccGSGdJk32ZbslqciG2dQN0mzg5ezN2b0gRTKGz65m9ai5Dwcre_SlpgUg8LoF5u7J_jS4MuCaeLAHD0KTg.jpg'
        self.crawl(
            url,
            callback=self.image_detail_page,
            save={'extension': 'jpg', 'filename': 'testimage.jpg'}
        )

    def image_detail_page(self, response):
        extension = response.save['extension']
        file_name = response.save['filename']
        file_path = os.path.join(self.DIR_PATH, file_name)
        content = response.content
        self.save_img(content, file_path)

    def on_message(self, project, message):
        if project == self.PROXY_UPDATER:
            # new proxy added
            proxy_host = message
            self.PROXY_POOL[proxy_host] = 0
        else:
            # should be index fetcher
            url = message.get('url')
            cookies = message.get('cookies')
            extension = message.get('ext')
            file_name = message.get('file_name')
            assert(url)
            self.crawl(
                url,
                cookies=cookies,
                proxy=random.choice(self._get_valid_proxies()),
                callback=self.image_detail_page,
                save={'extension': extension, 'filename': file_name}
            )

    def _get_valid_proxies(self):
        return [
            k for k, v in filter(
                lambda k, v: v < self.FAIL_THRESHOLD, self.PROXY_POOL.iteritems()
            )
        ]

    def save_img(self,content,path):
        f = open(path,"wb" )
        f.write(content)
        f.close()
