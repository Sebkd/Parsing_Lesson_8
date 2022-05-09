import re
from copy import deepcopy
from urllib.parse import urlencode

import scrapy
from scrapy.http import HtmlResponse

import setting_instagram
import setting_instagram_secret
from Instagramscraper.items import InstafollowdataItem


class InstafollowdataSpider(scrapy.Spider):
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
    followings_link = setting_instagram.FOLLOWINGS_LINK

    def parse(self, response: HtmlResponse):
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
        '''проходим по циклу список пользователей, у которых нужно собрать фоловверов '''
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
        print()
        '''Заходим на страницу пользователей и вызываем фолловеров'''
        user_id = self.fetch_id_parse_user(response.text)  # узнаем id пользователя

        variables = {
            'count': self.first_attr,
            'search_surface': 'follow_list_page',
            'max_id': 0,
        }
        url_followers = f'{self.friendship_link}{user_id}{self.followers_link}?{urlencode(variables)}'

        yield response.follow(
            url=url_followers,
            callback=self.parse_user_followers,
            cb_kwargs={
                'username': username,
                'variables': deepcopy(variables),
                'user_id': user_id,
            },
            headers={
                'User-Agent': 'Instagram 155.0.0.37.107',
            },
        )

    def parse_user_followers(self, response: HtmlResponse, username, user_id, variables):

        json_data = response.json()
        if json_data['next_max_id'] and int(json_data['next_max_id']) > variables['max_id']:
            variables['max_id'] = json_data['next_max_id']
            url_followers = f'{self.friendship_link}{user_id}{self.followers_link}?{urlencode(variables)}'
            print()
            yield response.follow(
                url=url_followers,
                callback=self.parse_user_followers,
                cb_kwargs={
                    'username': username,
                    'variables': deepcopy(variables),
                    'user_id': user_id,
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
            print()
            yield item

