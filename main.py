import logging, time, os, json
import asyncio

from vkwave.client import AIOHTTPClient
from vkwave.api import BotSyncSingleToken, Token, API
from vkwave.bots import (
    TokenStorage,
    Dispatcher,
    BotLongpollExtension,
    DefaultRouter,
    GroupId,
    EventTypeFilter,
)
from vkwave.types.bot_events import BotEventType
from vkwave.longpoll import BotLongpollData, BotLongpoll
from modules.storage import dump
from modules import basemaster as base, handle as hand, storage as stor, commands as co


async def main():
    path = os.path.dirname(os.path.abspath(__file__))
    with open(f"{path}/base/config{mode}.json", 'r') as file:
        dump_conf = json.load(file)
    stor.config = dump_conf.copy()
    bot_token = Token(dump_conf['TOKEN'])
    dump_conf['BASEFILE'] = f"{path}/base/{dump_conf['BASEFILE']}"
    dump_conf['LOGFILE'] = f"{path}/base/{dump_conf['LOGFILE']}"

    logging.basicConfig(level=11,filename=dump_conf['LOGFILE'])
    base_logger = logging.getLogger('base')
    base_logger.setLevel(10)
    command_logger = logging.getLogger('co')
    command_logger.setLevel(10)
    co.st.logger = command_logger

    client = AIOHTTPClient()
    token = BotSyncSingleToken(bot_token)
    api_session = API(token, client)
    api = api_session.get_context()
    lp_data = BotLongpollData(dump_conf['GROUP_ID'])
    longpoll = BotLongpoll(api, lp_data)
    token_storage = TokenStorage[GroupId]()
    dp = Dispatcher(api_session, token_storage)
    lp_extension = BotLongpollExtension(dp, longpoll)

    dp.add_router(await hand.initiate_router(DefaultRouter()))
    await base.initiate(dump_conf['BASEFILE'], base_logger)
    await dp.cache_potential_tokens()
    # await co.test_all()
    await lp_extension.start()



mode = 1



if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()

