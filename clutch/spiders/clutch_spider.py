# -*- coding: utf-8 -*-
import scrapy
import w3lib.url
import re

# Columns I need: Agency name, website URL, contact email, employee range, location


class ClutchSpiderSpider(scrapy.Spider):
    name = 'clutch_spider'
    allowed_domains = ['clutch.co']

    def start_requests(self):
        url = 'https://clutch.co/seo-firms'
        yield scrapy.Request(url, callback=self.parse, errback=self.on_error)

    def parse(self, response):
        def get_email_from_script(script_text):
            email = ''
            sp = script_text.split(';')  # split by code rows
            encoded_email_list = re.findall(r"'(.*@.*)'", sp[0])
            if len(encoded_email_list):
                split_email = encoded_email_list[0].split('#')
                indexes = re.findall(r"\[(\d)\]", sp[2])

                for idx in indexes:
                    email += split_email[int(idx)]

            return email

        # Is this right site? If not - repeat request
        if 'Clutch' not in response.xpath('//title/text()').get():
            self.logger.warning('It is not Clutch page')
            yield scrapy.Request(response.url, callback=self.parse, errback=self.on_error, dont_filter=True)

        for row in response.css('.provider-row'):
            base_info = row.css('.provider-base-info')
            detail_info = row.css('.provider-link-details')
            yield {
                'agency_name': base_info.css('h3.company-name a::text').get(),
                'website_url': w3lib.url.urljoin(detail_info.css('.website-link a').attrib['href'], '/'),

                'email': get_email_from_script(
                    detail_info.css('.contact-dropdown .item i.icon-mail').xpath('following-sibling::script').get('')
                ),
                'employees': base_info.css('span.employees::text').get(''),
                'city': base_info.css('.locality::text').get('')[:-1],
                'region': base_info.css('.region::text').get(''),
                'country': base_info.css('.country-name::text').get('USA')
            }

        next_page = response.css('.pager .pager-next a')
        if len(next_page):
           yield response.follow(next_page[0], callback=self.parse)

    def on_error(self, failure):
        pass
        # are we banned?
        # if failure.value.response.status == 403:
        #     self.logger.error("403 Error: {}".format(repr(failure)))
