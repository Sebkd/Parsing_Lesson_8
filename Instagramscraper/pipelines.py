# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import scrapy
from itemadapter import ItemAdapter
from pymongo import MongoClient
from scrapy.pipelines.images import ImagesPipeline


class InstagramscraperPipeline:
    def process_item(self, item, spider):
        return item


class InstafollowdataPipeline:
    def __init__(self):
        # не забывай включить процесс mongod.service
        # systemctl start mongod.service
        # systemctl status mongod.service
        client = MongoClient('localhost', 27017)
        self.mongobase = client.instafollow

    def process_item(self, item, spider):
        collection = self.mongobase[spider.name]
        collection.insert_one(item)
        return item


class InstafollowdataImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        # для работы необходима библиотека pillow
        if item['profile_pic']:
            try:
                yield scrapy.Request(item.get('profile_pic'))
            except Exception as error:
                print(error)


    def item_completed(self, results, item, info):
        item['profile_pic'] = [el[1] for el in results if el[0]]
        return item
