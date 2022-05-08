import scrapy


class InstafollowersspiderSpider(scrapy.Spider):
    name = 'instafollowersspider'
    allowed_domains = ['instagram.com']
    start_urls = ['http://instagram.com/']

    def parse(self, response):
        pass
