import logging
import requests
import sched
import functools
import hashlib
import sys

logger = logging.getLogger(__name__)


class WebMonitor:
    def __init__(self, url, parsers, changed_callback=None, interval=None, headers=None, last_data=None):
        self.url = url
        self.parsers = parsers or []

        def noop(*args, **kwargs): return None

        self.changed_callback = changed_callback if callable(changed_callback) else noop
        self.interval = interval if interval else 3*60
        self.headers = headers

        self.last_data = last_data

        self.scheduler = sched.scheduler()
        self.even = None
        self.sched_continue = functools.partial(self.scheduler.enter, self.interval, 1, self.request)

    def request(self):
        # url为空 或 parser为空直接跳过
        if not all((self.url, all((self.parsers),))):
            return

        # 发送请求并解析
        try:
            content = requests.get(self.url, headers=self.headers).content
            for parser in self.parsers:
                content = parser.parse(content)
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            logger.warning(e)
            content = None

        # 检查变更并通知
        if self.update_data(content):
            logger.info('data change to: ' + content)
            try:
                self.changed_callback(content)
            except KeyboardInterrupt:
                sys.exit(1)
            except Exception as e:
                logger.warning(e)
        self.even = self.sched_continue()

    def update_data(self, data):
        if isinstance(data, str):
            data = data.encode()
        hash = hashlib.sha256(data).hexdigest()
        if self.last_data != hash:
            self.last_data = hash
            return True
        else:
            return False

    def start(self):
        self.even = self.sched_continue()
        self.scheduler.run()

    def stop(self):
        if self.even is not None:
            self.scheduler.cancel(self.even)
