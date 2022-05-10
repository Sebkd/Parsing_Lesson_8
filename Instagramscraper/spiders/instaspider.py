import json
import re

from urllib.parse import urlencode
import scrapy
from scrapy.http import HtmlResponse
from copy import deepcopy

import setting_instagram
import setting_instagram_secret
from Instagramscraper.items import InstagramscraperItem


class InstaspiderSpider(scrapy.Spider):
    name = 'instaspider'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com']

    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = setting_instagram_secret.LOGIN_INSTAGRAM
    inst_pwd = setting_instagram_secret.PASS_INSTAGRAM
    inst_parse_users = setting_instagram.INSTAGRAM_PARSE_USERS
    graphql_url = setting_instagram.GRAPHQL_URL
    query_hash = setting_instagram.QUERY_HASH
    first_attr = setting_instagram.FIRST_ATTR

    def parse(self, response: HtmlResponse):
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

    def fetch_user_id(self, text, username):
        """Получение id пользователя, которого парсят из кода HTML страницы
         (вариант преподавателя)"""
        try:
            match = re.search(
                '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
            ).group()
            return json.loads(match).get('id')
        except:
            return re.findall('\"id\":\"\\d+\"', text)[-1].split('"')[-2]

    def parse_inst_user(self, response: HtmlResponse, username):
        user_id = self.fetch_id_parse_user(response.text)
        user_id_variant_teacher = self.fetch_user_id(response.text, username=username)

        variables = {
            'id': user_id,
            'first': self.first_attr
        }
        url_posts = f'{self.graphql_url}query_hash={self.query_hash}&{urlencode(variables)}'

        yield response.follow(
            url_posts,
            callback=self.parse_user_posts,
            cb_kwargs={
                'username': username,
                'user_id': user_id,
                'variables': deepcopy(variables)
            },
        )

    def parse_user_posts(self, response: HtmlResponse, username, user_id, variables):

        json_data = response.json()
        page_info = json_data.get('data').get('user').get('edge_owner_to_timeline_media').get('page_info')

        if page_info['has_next_page']:
            variables['after'] = page_info['end_cursor']

            url_posts = f'{self.graphql_url}query_hash={self.query_hash}&{urlencode(variables)}'

            yield response.follow(
                url_posts,
                callback=self.parse_user_posts,
                cb_kwargs={
                    'username': username,
                    'user_id': user_id,
                    'variables': deepcopy(variables)
                },
            )

        posts = json_data.get('data').get('user').get('edge_owner_to_timeline_media').get('edges')
        for post in posts:
            item = InstagramscraperItem(
                user_id=user_id,
                username=username,
                photo=post.get('node').get('display_url'),
                likes=post.get('node').get('edge_media_preview_like').get('count'),
                post_data=post.get('node')
            )
            print()
            yield item
