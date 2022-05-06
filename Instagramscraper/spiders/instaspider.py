import scrapy
from scrapy.http import HtmlResponse


class InstaspiderSpider(scrapy.Spider):
    name = 'instaspider'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com']

    def parse(self, response: HtmlResponse):
        pass
