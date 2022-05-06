import re

import scrapy
from scrapy.http import HtmlResponse

import setting_instagram


class InstaspiderSpider(scrapy.Spider):
    name = 'instaspider'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com']

    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = setting_instagram.LOGIN_INSTAGRAM
    inst_pwd = setting_instagram.PASS_INSTAGRAM
    inst_parse_user = setting_instagram.INSTAGRAM_PARSE_USER

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
            yield response.follow(f'/{self.inst_parse_user}/',
                                  callback=self.parse_inst_user,
                                  cb_kwargs={
                                      'username': self.inst_parse_user
                                  },
                                  )

    @staticmethod
    def fetch_csrf_token(text):
        """Получение CSRF токена для авторизации из кода HTML страницы"""
        match = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return match.split(':').pop().replace(r'"', '')

    def parse_inst_user(self, response: HtmlResponse, username):
        print()
