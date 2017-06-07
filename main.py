from ElpamBot import ElpamBot
from Parser import Parser
from WebMonitor import WebMonitor
import configparser
import time


def get_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)

    assert 'Bot' in config.sections(), 'Bot section must not None!'
    assert 'token' in config['Bot'], 'token in Bot must not None!'

    assert 'WebMonitor' in config.sections(), 'WebMonitor must not None!'
    assert 'url' in config['WebMonitor'], 'url in WebMonitor must not None!'

    if 'Subscribers' not in config.sections():
        config.add_section('Subscribers')

    return config


def update_config(config):
    with open('ElpamBot.ini', 'w', buffering=1) as fp:
        config.write(fp)


def main():
    config_file_path = 'ElpamBot.ini'
    config = get_config(config_file_path)

    bot_config = config['Bot']
    web_monitor_config = config['WebMonitor']

    parser_configs = []
    for section in config.sections():
        if section.startswith('Parser'):
            parser_configs.append(config[section])

    subscribers_section = config['Subscribers']

    # init bot
    receivers = set(map(int, subscribers_section.keys()))
    elpam_bot = ElpamBot(bot_config.get('token'), proxy=bot_config.get('proxy'), receivers=receivers)

    # 用户订阅消息回调
    @elpam_bot.event_receiver('subscribe')
    def on_subscribe(message):
        chat_id = str(message.chat_id)
        if chat_id not in subscribers_section.keys():
            data = {
                'id': message.chat.id,
                'type': message.chat.type,
                'username': message.chat.username,
                'first_name': message.chat.first_name,
                'timestamp': int(time.time()),
            }
            config.set('Subscribers', chat_id, str(data))
            # TODO fix 线程同步
            update_config(config)

    @elpam_bot.event_receiver('unsubscribe')
    def on_unsubscribe(message):
        chat_id = str(message.chat_id)
        if chat_id in subscribers_section.keys():
            config.remove_option('Subscribers', chat_id)
            # TODO fix 线程同步
            update_config(config)

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
        config.set('WebMonitor', 'last_data', monitor.last_data or '')
        update_config(config)

    last_data = web_monitor_config.get('last_data')

    monitor = WebMonitor(url, parsers, changed_callback=changed_callback, interval=interval, headers=headers, last_data=last_data)

    # start bot
    elpam_bot.start(blocking=False)
    monitor.start()


if __name__ == '__main__':
    main()
