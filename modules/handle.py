import time

from vkwave.bots import (
    TokenStorage,
    Dispatcher,
    BotLongpollExtension,
    DefaultRouter,
    GroupId,
    EventTypeFilter,
    ChatActionFilter,
    CommandsFilter,
)
from vkwave.types.objects import MessagesMessageActionStatus
from vkwave.types.bot_events import BotEventType
from vkwave.bots.core.dispatching.filters.base import BaseFilter, BaseEvent, FilterResult
import modules.storage as stor
import modules.basemaster as base
from modules.databox import DataBox
from modules.commands import (
    kick,
    broadcast,
    utils,
    checkuser,
    test,
    chatcontrol,
)

command_dict = {
    'kick' : {'obj' : kick.kick, 'level' : 1},
    'broadcast' : {'obj' : broadcast.broadcast, 'level' : 1},
    't' : {'obj' : test.test, 'level' : 1},
    'op' : {'obj' : chatcontrol.add_admin, 'level' : 1},
    'deop' : {'obj' : chatcontrol.del_admin, 'level' : 1},
    'addchat' : {'obj' : chatcontrol.add_chat, 'level' : 1},
    'delchat' : {'obj' : chatcontrol.del_chat, 'level' : 1}
}



async def new_user(event):
    box = DataBox(event)
    if box.msg.action.type is MessagesMessageActionStatus.CHAT_INVITE_USER:
        user_id = box.msg.action.member_id
    elif box.msg.action.type is MessagesMessageActionStatus.CHAT_INVITE_USER_BY_LINK:
        user_id = box.msg.from_id
    await checkuser.check_all(box, user_id)
    return str(user_id)
    pass

async def simple(event):
    box = DataBox(event)
    await test.test(box)

async def command(event):
    box = DataBox(event)
    if box.command in command_dict.keys():
        if box.admin_level >= command_dict[box.command]['level']:
            try:
                await command_dict[box.command]['obj'](box)
            except Exception as e:
                raise SystemExit(e)
    if box.admin_level == 0:
        await simple(event)

class CommandFilter(BaseFilter):
    def __init__(self):
        pass

    async def check(self, event:BaseEvent) -> FilterResult:
        text = event.object.object.message.text.lower()
        from_id = event.object.object.message.from_id
        peer_id = event.object.object.message.peer_id
        result = False
        if text.startswith(f"[club{event.object.group_id}|"):
            result = True
        elif text.startswith("do") and peer_id == from_id:
            result = True
        return FilterResult(result)

async def initiate_router(router):
    router.registrar.register(
        router.registrar.new()
        .with_filters(
            ChatActionFilter(MessagesMessageActionStatus.CHAT_INVITE_USER) |
            ChatActionFilter(MessagesMessageActionStatus.CHAT_INVITE_USER_BY_LINK)
        )
        .handle(new_user)
        .ready()
    )

    router.registrar.register(
        router.registrar.new()
        .with_filters(
            EventTypeFilter('message_new') &
            CommandFilter()
        )
        .handle(command)
        .ready()
    )

    router.registrar.register(
        router.registrar.new()
        .with_filters(
            EventTypeFilter('message_new')
        )
        .handle(simple)
        .ready()
    )
    return router
