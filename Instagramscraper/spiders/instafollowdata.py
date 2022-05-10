"""
Модуль парсинга данных: ввод данных в item без предварительной обработки
Парсим данные по follower и following
"""
import re
from copy import deepcopy
from urllib.parse import urlencode

import scrapy
from scrapy.http import HtmlResponse

import setting_instagram

import setting_instagram_secret
from Instagramscraper.items import InstafollowdataItem


class InstafollowdataSpider(scrapy.Spider):
    """
    класс парсинга данных с необходимыми методами.
    Выход объект item
    """
    name = 'instafollowdata'
    allowed_domains = ['instagram.com']
    start_urls = ['http://instagram.com/']

    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = setting_instagram_secret.LOGIN_INSTAGRAM
    inst_pwd = setting_instagram_secret.PASS_INSTAGRAM
    inst_parse_users = setting_instagram.INSTAGRAM_PARSE_USERS
    graphql_url = setting_instagram.GRAPHQL_URL
    query_hash = setting_instagram.QUERY_HASH
    first_attr = setting_instagram.FIRST_ATTR
    count = setting_instagram.COUNT

    friendship_link = setting_instagram.FRIENDSHIP_LINK
    followers_link = setting_instagram.FOLLOWERS_LINK
    following_link = setting_instagram.FOLLOWING_LINK

    def parse(self, response: HtmlResponse, **kwargs):
        # логинимся
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_link,
            method='POST',
            callback=self.login,
            formdata={
                'username': self.inst_login,
                'enc_password': self.inst_pwd,
            },
            headers={
                'X-CSRFToken': csrf,
            },
        )

    def login(self, response: HtmlResponse):
        """проходим по циклу список пользователей, у которых нужно собрать фоловверов """
        json_body = response.json()
        if json_body['authenticated']:
            # здесь можно сделать цикл из пользователей которых парсим
            for user in self.inst_parse_users:
                yield response.follow(f'/{user}/',
                                      callback=self.parse_inst_user,
                                      cb_kwargs={
                                          'username': user
                                      },
                                      )

    @staticmethod
    def fetch_csrf_token(text):
        """Получение CSRF токена для авторизации из кода HTML страницы"""
        match = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return match.split(':').pop().replace(r'"', '')

    @staticmethod
    def fetch_id_parse_user(text):
        """Получение id пользователя, которого парсят из кода HTML страницы"""
        match = re.search('\"profilePage_\\w+\"', text).group()
        return match.replace(r'profilePage_', '').replace(r'"', '')

    def parse_inst_user(self, response: HtmlResponse, username):
        """
        Функция первых вызовов данных с api
        :param response: ответ от сервера
        :param username: пользователь, на странице которого смотрим follower and following
        :return: генераторы вызова функций парсинга
        """
        user_id = self.fetch_id_parse_user(response.text)  # узнаем id пользователя

        variables = {
            'count': self.first_attr,
            'search_surface': 'follow_list_page',
            # 'max_id': 0,
        }
        url_followers = f'{self.friendship_link}{user_id}' \
                        f'{self.followers_link}?{urlencode(variables)}'
        yield response.follow(
            url=url_followers,
            callback=self.parse_user_followers,
            cb_kwargs={
                'username': username,
                'variables': deepcopy(variables),
                'user_id': user_id,
                'counter': 0,
            },
            headers={
                'User-Agent': 'Instagram 155.0.0.37.107'
            },
        )

        variables_following = {
            'count': self.first_attr,
            'max_id': 0,
        }
        url_following = f'{self.friendship_link}{user_id}' \
                        f'{self.following_link}?{urlencode(variables_following)}'
        yield response.follow(
            url=url_following,
            callback=self.parse_user_following,
            cb_kwargs={
                'username': username,
                'variables_following': deepcopy(variables_following),
                'user_id': user_id,
            },
            headers={
                'User-Agent': 'Instagram 155.0.0.37.107',
            },
        )

    def parse_user_followers(self, response: HtmlResponse, username, user_id, counter, variables):
        """
        Функция вторичных вызовов follower, поставлено ограничение не более 30шт,
         Instagram блокирует. Также Instagram в формате Json передает значение 'next_max_id' как
         кодированное, поэтому прежний формат не работает.
        :param counter: подсчет старничек по 12 пользователй, чтобы не заблокировал Instagram
        :param response: ответ от сервера
        :param username: имя пользователя страницы
        :param user_id: id пользователя страницы
        :param variables: необходимый набор данных для формирования
        :return: генератор создания item
        """
        if variables.get('max_id') is None:
            variables['max_id'] = ''

        json_data = response.json()
        # if json_data['next_max_id'] \
        #         and variables['max_id'] < int(json_data['next_max_id']) < 30:
        if json_data['next_max_id'] and counter < 24:
            variables['max_id'] = json_data['next_max_id']
            counter += 12
            # variables['max_id'] = int(json_data['next_max_id'])
            url_followers = f'{self.friendship_link}{user_id}' \
                            f'{self.followers_link}?{urlencode(variables)}'
            yield response.follow(
                url=url_followers,
                callback=self.parse_user_followers,
                cb_kwargs={
                    'username': username,
                    'variables': deepcopy(variables),
                    'user_id': user_id,
                    'counter': counter,
                },
                headers={
                    'User-Agent': 'Instagram 155.0.0.37.107',
                },
            )

        followers = json_data.get('users')
        for follower in followers:
            item = InstafollowdataItem(
                user_id=follower.get('pk'),
                username=follower.get('username'),
                follower_cursor=username,
                following_cursor='',
                profile_pic=follower.get('profile_pic_url'),
                post_data=follower,
            )
            yield item

    def parse_user_following(self, response: HtmlResponse, username, user_id, variables_following):
        """
        Функция вторичных вызовов folling, поставлено ограничение не более 30шт,
         Instagram блокирует
        :param response: ответ от сервера
        :param username: имя пользователя страницы
        :param user_id: id пользователя страницы
        :param variables_following: необходимый набор данных для формирования
        :return: генератор создания item
        """
        json_data = response.json()
        if json_data['next_max_id'] \
                and variables_following['max_id'] < int(json_data['next_max_id']) < 30:
            variables_following['max_id'] = int(json_data['next_max_id'])
            url_following = f'{self.friendship_link}{user_id}{self.following_link}' \
                            f'?{urlencode(variables_following)}'

            yield response.follow(
                url=url_following,
                callback=self.parse_user_following,
                cb_kwargs={
                    'username': username,
                    'variables_following': deepcopy(variables_following),
                    'user_id': user_id,
                },
                headers={
                    'User-Agent': 'Instagram 155.0.0.37.107',
                },
            )

        followings = json_data.get('users')
        for following in followings:
            item = InstafollowdataItem(
                user_id=following.get('pk'),
                username=following.get('username'),
                follower_cursor='',
                following_cursor=username,
                profile_pic=following.get('profile_pic_url'),
                post_data=following,
            )
            yield item
