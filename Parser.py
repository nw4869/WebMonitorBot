import re
from bs4 import BeautifulSoup


class Parser:
    def parse(self, string):
        raise NotImplementedError

    @staticmethod
    def create_parser(type, *args, **kwargs):
        if type == 'regex':
            return RegexParser(*args, **kwargs)
        elif type == 'replace':
            return ReplaceParser(*args, **kwargs)
        elif type == 'css':
            raw = kwargs.get('raw')
            if isinstance(raw, str):
                kwargs['raw'] = raw.lower() in ['true', 't', '1', 'y', 'yes']
            return CssParser(*args, **kwargs)


class RegexParser(Parser):
    def __init__(self, pattern):
        self.pattern = pattern

    def parse(self, string):
        if isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern)
        m = self.pattern.search(string)
        return m.group() if m else None


class ReplaceParser(Parser):
    def __init__(self, pattern, repl):
        self.pattern = pattern
        self.repl = repl

    def parse(self, string):
        if isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern)
        return self.pattern.sub(self.repl, string)


class CssParser(Parser):
    def __init__(self, selector, raw=False):
        self.selector = selector
        self.raw = raw

    def parse(self, string):
        soup = BeautifulSoup(string, 'html.parser')
        item = soup.select_one(self.selector)
        if item is None:
            return None
        elif self.raw:
            return str(item)
        else:
            return item.text
