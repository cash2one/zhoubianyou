#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-10-21 01:46:53
# Project: update_proxy

from pyspider.libs.base_handler import *
import logging
import uuid

logger = logging.getLogger(__name__)


class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
        }
    }

    PROXY_USERS = ['nf_zhoubianyou', 'gat_zhoubianyou', 'comment_fetcher', 'image_fetcher']
    PAGES = 10  # 只抓取10页匿名代理
    TEST_URL = 'http://www.baidu.com'

    @every(minutes=60)
    def on_start(self):
        for page in range(self.PAGES):
            self.crawl(
                'http://www.kuaidaili.com/free/inha/{p}/'.format(p=page+1),
                callback=self.proxy_list_page,
                age=300,  # seconds
                auto_recrawl=True
            )
            self.crawl(
                'http://www.kuaidaili.com/free/intr/{p}/'.format(p=page+1),
                callback=self.proxy_list_page,
                age=300,  # seconds
                auto_recrawl=True
            )

    def proxy_list_page(self, response):
        proxy_item_selector = '#list > table > tbody > tr'
        for proxy_item in response.doc(proxy_item_selector).items():
            ip_col_selector = 'td:nth-child(1)'
            port_col_selector = 'td:nth-child(2)'
            type_col_selector = 'td:nth-child(4)'
            ip = proxy_item(ip_col_selector).text()
            port = proxy_item(port_col_selector).text()
            http_type = proxy_item(type_col_selector).text()
            logger.info(ip + ':' + port)
            if http_type and http_type.lower() == 'http':
                proxy_host = '{ip}:{port}'.format(ip=ip, port=port)
                # test proxy
                self.crawl(
                    self.TEST_URL,
                    proxy=proxy_host,
                    callback=self.test_proxy_result,
                    last_modified=False,
                    taskid=md5string(unicode(uuid.uuid4())),
                    save={
                        'proxy_host': proxy_host
                    }
                )

    @catch_status_code_error
    def test_proxy_result(self, response):
        proxy_host = response.save['proxy_host']
        if response.ok:
            # test success
            for project in self.PROXY_USERS:
                self.send_message(project, proxy_host, proxy_host)
            return {'proxy': proxy_host}
        # test fail, ignore proxy_host
        logger.warn('test proxy fail, ignore: {host}'.format(host=proxy_host))
