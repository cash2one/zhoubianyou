from pyspider.libs.base_handler import *


class LocationCollectorHandler(BaseHandler):
    START_PAGE = 'http://www.dianping.com/search/category/2/35'

    crawl_config = {
    }

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl(self.START_PAGE, callback=self.index_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            self.crawl(each.attr.href, callback=self.detail_page)

    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc('title').text(),
        }
