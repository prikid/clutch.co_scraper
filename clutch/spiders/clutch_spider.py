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
        # url = 'https://clutch.co/seo-firms?page=12'
        # url = 'https://clutch.co/seo-firms?sort_by=field_pp_page_sponsor&field_pp_min_project_size=All&field_pp_hrly_rate_range=All&field_pp_size_people=All&field_pp_cs_small_biz=&field_pp_cs_midmarket=&field_pp_cs_enterprise=&client_focus=&field_pp_if_advertising=&field_pp_if_automotive=&field_pp_if_arts=&field_pp_if_bizservices=&field_pp_if_conproducts=&field_pp_if_education=&field_pp_if_natural_resources=&field_pp_if_finservices=&field_pp_if_gambling=&field_pp_if_gaming=&field_pp_if_government=&field_pp_if_healthcare=&field_pp_if_hospitality=&field_pp_if_it=&field_pp_if_legal=&field_pp_if_manufacturing=&field_pp_if_media=&field_pp_if_nonprofit=&field_pp_if_realestate=&field_pp_if_retail=&field_pp_if_telecom=&field_pp_if_transportation=&field_pp_if_utilities=&field_pp_if_other=&industry_focus=&field_pp_location_country_select=vn&field_pp_location_province=&field_pp_location_latlon_1%5Bpostal_code%5D=&field_pp_location_latlon_1%5Bsearch_distance%5D=100&field_pp_location_latlon_1%5Bsearch_units%5D=mile'
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
