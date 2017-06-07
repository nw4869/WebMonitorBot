import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from functools import wraps

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class ElpamBot:
    def __init__(self, token, proxy=None, receivers=None):
        self.updater = Updater(token=token, request_kwargs={'proxy_url': proxy or ''})

        self.receivers = receivers or set()
        # self.receivers.add(374440130)

        self.last_data = None

        self.subscribe_listeners = []
        self.unsubscribe_listeners = []

        # decorator:不用每定义一个函数都要用handler以及add_handler
        def handler(handler, cmd=None, **kw):
            def decorator(func):
                @wraps(func)
                def wrapper(*args, **kw):
                    return func(*args, **kw)

                if cmd is None:
                    func_handler = handler(func, **kw)
                else:
                    func_handler = handler(cmd, func, **kw)
                    self.updater.dispatcher.add_handler(func_handler)
                return wrapper

            return decorator

        @handler(CommandHandler, 'start')
        def start(bot, update):
            logger.info('/start: ' + str(update.message.chat_id))
            update.message.reply_text('Hi!')

        @handler(CommandHandler, 'help')
        def help(bot, update):
            update.message.reply_text('Help!')

        @handler(CommandHandler, 'subscribe')
        def subscribe(bot, update):
            if update.message.chat_id not in self.receivers:
                self.receivers.add(update.message.chat_id)
                for listener in self.subscribe_listeners:
                    listener(update.message)
                update.message.reply_text('subscribe succeeded!')
                logger.info('new subscriber: {0}'.format(update.message.chat))
            else:
                update.message.reply_text('already subscribed')

        @handler(CommandHandler, 'unsubscribe')
        def unsubscribe(bot, update):
            if update.message.chat_id in self.receivers:
                self.receivers.remove(update.message.chat_id)
                for listener in self.unsubscribe_listeners:
                    listener(update.message)
                update.message.reply_text('unsubscribe succeeded!')
                logger.info('remove subscriber: {0}'.format(update.message.chat_id))
            else:
                update.message.reply_text('not subscribe')

        @handler(MessageHandler, Filters.text)
        def echo(bot, update):
            update.message.reply_text(update.message.text)

        @handler(CommandHandler, 'last')
        def last_data(bot, update):
            data = self.last_data if self.last_data else 'Nothing.'
            update.message.reply_text(data, parse_mode=telegram.ParseMode.HTML)

        def error(bot, update, error):
            logger.warning('Update "%s" caused error "%s"' % (update, error))
        self.updater.dispatcher.add_error_handler(error)

    def notify(self, msg):
        logger.info('notify to receivers: ' + str(self.receivers))
        self.last_data = msg
        for chat_id in self.receivers:
            self.updater.bot.send_message(chat_id, msg, parse_mode=telegram.ParseMode.HTML)

    def event_receiver(self, type, **kwargs):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)

            if type == 'subscribe':
                if func not in self.subscribe_listeners:
                    self.subscribe_listeners.append(func)
            elif type == 'unsubscribe':
                if func not in self.unsubscribe_listeners:
                    self.unsubscribe_listeners.append(func)
            else:
                logger.warning('type not found: ' + type)
            return wrapper
        return decorator

    def start(self, blocking=True):
        self.updater.start_polling()
        logger.info('started')
        if blocking:
            self.updater.idle()
