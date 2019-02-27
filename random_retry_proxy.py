# Daniil Mashkin <daniil.mashkin@gmail.com> (2016)
# based on https://github.com/aivarsk/scrapy-proxies

import re
import random
import base64
import logging
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.python import global_object_name

logger = logging.getLogger(__name__)


class Mode:
    RANDOMIZE_PROXY_EVERY_REQUESTS, RANDOMIZE_PROXY_ONCE, SET_CUSTOM_PROXY = range(3)


class RandomProxyRetryMiddleware(RetryMiddleware):
    def __init__(self, settings):
        RetryMiddleware.__init__(self, settings)

        self.mode = settings.get('PROXY_MODE')
        self.proxy_list = settings.get('PROXY_LIST')
        self.chosen_proxy = ''

        if self.mode == Mode.RANDOMIZE_PROXY_EVERY_REQUESTS or self.mode == Mode.RANDOMIZE_PROXY_ONCE:
            if self.proxy_list is None:
                raise KeyError('PROXY_LIST setting is missing')
            self.proxies = {}
            fin = open(self.proxy_list)
            try:
                for line in fin.readlines():
                    parts = re.match('(\w+://)(\w+:\w+@)?(.+)', line.strip())
                    if not parts:
                        continue

                    # Cut trailing @
                    if parts.group(2):
                        user_pass = parts.group(2)[:-1]
                    else:
                        user_pass = ''

                    self.proxies[parts.group(1) + parts.group(3)] = user_pass
            finally:
                fin.close()
            if self.mode == Mode.RANDOMIZE_PROXY_ONCE:
                self.chosen_proxy = random.choice(list(self.proxies.keys()))
        elif self.mode == Mode.SET_CUSTOM_PROXY:
            custom_proxy = settings.get('CUSTOM_PROXY')
            self.proxies = {}
            parts = re.match('(\w+://)([^:]+?:[^@]+?@)?(.+)', custom_proxy.strip())
            if not parts:
                raise ValueError('CUSTOM_PROXY is not well formatted')

            if parts.group(2):
                user_pass = parts.group(2)[:-1]
            else:
                user_pass = ''

            self.proxies[parts.group(1) + parts.group(3)] = user_pass
            self.chosen_proxy = parts.group(1) + parts.group(3)


    def process_request(self, request, spider):
        # Don't overwrite with a random one (server-side state for IP)
        if 'proxy' in request.meta:
            return

        self.change_proxy(request)

    def change_proxy(self, request):
        if len(self.proxies) == 0:
            raise ValueError('All proxies are unusable, cannot proceed')

        if self.mode == Mode.RANDOMIZE_PROXY_EVERY_REQUESTS:
            proxy_address = random.choice(list(self.proxies.keys()))
        else:
            proxy_address = self.chosen_proxy

        proxy_user_pass = self.proxies[proxy_address]

        request.meta['proxy'] = proxy_address
        if proxy_user_pass:
            basic_auth = 'Basic ' + base64.b64encode(proxy_user_pass.encode()).decode()
            request.headers['Proxy-Authorization'] = basic_auth

    def _get_retry_request(self, request, retry_times):
        retryreq = request.copy()
        retryreq.meta['retry_times'] = retry_times
        retryreq.dont_filter = True
        retryreq.priority = request.priority + self.priority_adjust
        return retryreq


    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1

        retry_times = self.max_retry_times

        if 'max_retry_times' in request.meta:
            retry_times = request.meta['max_retry_times']

        stats = spider.crawler.stats
        proxy = request.meta['proxy']

        if retries <= retry_times:
            logger.debug("Retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})

            # logger.debug('Retrying proxy <%s> #%d: %s' % (proxy, retries, reason))

            retryreq = self._get_retry_request(request, retries)

            if isinstance(reason, Exception):
                reason = global_object_name(reason.__class__)

            stats.inc_value('retry/count')
            stats.inc_value('retry/reason_count/%s' % reason)
        else:
            stats.inc_value('retry/max_reached')
            logger.debug("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                          extra={'spider': spider})

            # try:

            del self.proxies[proxy]
            retryreq = self._get_retry_request(request, 0)
            self.change_proxy(retryreq)
            logger.error('Removing proxy <%s>, %d proxies left' % (proxy, len(self.proxies)))

            # except (ValueError, KeyError):
            #     pass

        return retryreq
