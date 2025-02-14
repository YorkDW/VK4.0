import logging, time, os, json, asyncio, vkwave, datetime
 
from vkwave.bots.core.dispatching.extensions.callback import AIOHTTPCallbackExtension
from vkwave.bots.core.dispatching.extensions.callback.conf import ConfirmationStorage

from vkwave.client import AIOHTTPClient
from vkwave.api.token.token import UserSyncSingleToken
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
# from base import baseCreation as bb
from modules import basemaster as base, handle as hand, storage as stor
from modules.commands import (
    utils,
    test,
)


async def main():
    # await bb.start()
    # stor.asyncio_loop.stop()
    # return 

    path = os.path.dirname(os.path.abspath(__file__))
    full_path = f"{path}/base/config{mode}.json"
    with open(full_path, 'r') as file:
        stor.config = json.load(file)
    bot_tokens = Token(stor.config['TOKEN'])
    user_tokens = Token(stor.config['USER_TOKEN'])
    stor.config['BASEFILE'] = f"{path}/base/{stor.config['BASEFILE']}"
    stor.config['LOGFILE'] = f"{path}/base/{stor.config['LOGFILE']}"
    stor.config['CONFIG'] = full_path

    logging.basicConfig(level=stor.config['LOGLEVEL'],filename=stor.config['LOGFILE'])
    logging.addLevelName(11,'OK')
    logging.addLevelName(12,'DONE')
    logging.addLevelName(13,'NO')
    logging.addLevelName(14,'BAD')

    base_logger = logging.getLogger('base')
    command_logger = logging.getLogger('co')
    utils.st.logger = command_logger

    stor.start_time = int(time.time())

    user_client = AIOHTTPClient()
    user_tokens = [UserSyncSingleToken(tok) for tok in user_tokens]
    stor.user_api = API(user_tokens, user_client)
    
    client = AIOHTTPClient()
    tokens = [BotSyncSingleToken(tok) for tok in bot_tokens]
    api_session = API(tokens, client)
    api = api_session.get_context()
    lp_data = BotLongpollData(stor.config['GROUP_ID'])
    longpoll = BotLongpoll(api, lp_data)
    token_storage = TokenStorage[GroupId]()
    dp = Dispatcher(api_session, token_storage)
    dp.add_router(await hand.initiate_router(DefaultRouter()))
    await dp.cache_potential_tokens()
    await base.initiate(stor.config['BASEFILE'], base_logger)

    # storage = ConfirmationStorage()
    # storage.add_confirmation(GroupId(stor.config['GROUP_ID']),stor.config['CONFIRMATION'])
    # cb_extension = AIOHTTPCallbackExtension(
    #     dp, path="/", host="0.0.0.0", port=80, secret=stor.config['SECRET'], confirmation_storage=storage
    # )

    lp_extension = BotLongpollExtension(dp, longpoll)
    
    # await cb_extension.start()
    await lp_extension.start()


mode = 2



if __name__ == "__main__":
    stor.asyncio_loop = asyncio.get_event_loop()
    stor.asyncio_loop.create_task(main())
    stor.asyncio_loop.run_forever()

