from ElpamBot import ElpamBot
from Parser import Parser
from WebMonitor import WebMonitor
import configparser


def get_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)

    assert 'Bot' in config.sections(), 'Bot section must not None!'
    assert 'token' in config['Bot'], 'token in Bot must not None!'

    assert 'WebMonitor' in config.sections(), 'WebMonitor must not None!'
    assert 'url' in config['WebMonitor'], 'url in WebMonitor must not None!'

    return config


def main():
    config = get_config('ElpamBot.ini')

    bot_config = config['Bot']
    web_monitor_config = config['WebMonitor']

    parser_configs = []
    for section in config.sections():
        if section.startswith('Parser'):
            parser_configs.append(config[section])

    # init bot
    elpam_bot = ElpamBot(bot_config.get('token'), proxy=bot_config.get('proxy'))

    # init parsers
    parsers = []
    for parser_config in parser_configs:
        parsers.append(Parser.create_parser(**dict(parser_config)))

    # init web monitor
    headers = {}
    user_agent = web_monitor_config.get('user_agent')
    if user_agent:
        headers['User-Agent'] = user_agent

    url = web_monitor_config.get('url')
    interval = web_monitor_config.getint('interval')

    def changed_callback(data):
        elpam_bot.notify(data)
        config.set('WebMonitor', 'last_data', monitor.last_data)
        with open('ElpamBot.ini', 'w', buffering=1) as fp:
            config.write(fp)

    last_data = web_monitor_config.get('last_data')

    monitor = WebMonitor(url, parsers, changed_callback=changed_callback, interval=interval, headers=headers, last_data=last_data)

    # start bot
    elpam_bot.start(blocking=False)
    monitor.start()


if __name__ == '__main__':
    main()
