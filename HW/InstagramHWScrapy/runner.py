from scrapy.crawler import CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils.log import configure_logging
from twisted.internet import reactor

from HW.InstagramHWScrapy import settings
from HW.InstagramHWScrapy.spiders.instafollowersspider import InstafollowersspiderSpider

if __name__ == '__main__':  # ctrl+j main

    configure_logging()

    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    runner = CrawlerRunner(settings=crawler_settings)

    runner.crawl(InstafollowersspiderSpider)


    d = runner.join()
    d.addBoth(lambda _: reactor.stop())

    reactor.run()
