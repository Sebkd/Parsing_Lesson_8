"""
4) Написать запрос к базе, который вернет список подписчиков только указанного пользователя
5) Написать запрос к базе, который вернет список профилей, на кого подписан указанный пользователь
"""
from pymongo import MongoClient

from Instagramscraper.spiders.instafollowdata import InstafollowdataSpider


class Master:
    """
    Объект связи parser с БД
    """
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongobase = client.instafollow
        self.collection = None

    def set_collection(self, spider):
        """
        Установка коллекции
        :param spider: применяемый spider
        :return: привязка коллекции по имени парсера
        """
        self.collection = self.mongobase[spider.name]

    def request_follower_from_db(self, instagram_user):
        """
        Написать запрос к базе, который вернет список подписчиков только указанного пользователя
        :return:
        """
        if self.collection is None:
            return print('Не установлена коллекция')
        response_from_collection = self.collection.find({'follower_cursor': instagram_user})
        return response_from_collection

    def request_following_from_db(self, instagram_user):
        """
        Написать запрос к базе, который вернет список подписчиков только указанного пользователя
        :return:
        """
        if self.collection is None:
            return print('Не установлена коллекция')
        response_from_collection = self.collection.find({'following_cursor': instagram_user})
        return response_from_collection


if __name__ == '__main__':
    USERNAME = 'avangardmeb'
    data = Master()
    data.set_collection(InstafollowdataSpider)
    list_followers = [d for d in data.request_follower_from_db(instagram_user=USERNAME)]
    list_following = [d for d in data.request_following_from_db(instagram_user=USERNAME)]
    print(f'Followers пользователя {USERNAME}:', list_followers)
    print('----------------------------------------------------------------')
    print(f'Following пользователя {USERNAME}:', list_following)
    print('----------------------------------------------------------------')
