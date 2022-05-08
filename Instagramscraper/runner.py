from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils.log import configure_logging
from twisted.internet import reactor

from Instagramscraper import settings
from Instagramscraper.spiders.instafollowdata import InstafollowdataSpider
from Instagramscraper.spiders.instaspider import InstaspiderSpider

if __name__ == '__main__':  # ctrl+j main

    configure_logging()

    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    runner = CrawlerRunner(settings=crawler_settings)

    # runner.crawl(InstaspiderSpider)
    runner.crawl(InstafollowdataSpider)


    d = runner.join()
    d.addBoth(lambda _: reactor.stop())

    reactor.run()
