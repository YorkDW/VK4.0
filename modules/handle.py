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


from modules.basemaster import DataBox
import modules.commands as co

import inspect

command_dict = {
    'kick' : {'obj' : co.kick, 'level' : 1}
}



async def new_user(event):
    box = DataBox(event)
    if box.msg.action.type is MessagesMessageActionStatus.CHAT_INVITE_USER:
        user_id = box.msg.action.member_id
    elif box.msg.action.type is MessagesMessageActionStatus.CHAT_INVITE_USER_BY_LINK:
        user_id = box.msg.from_id
    await co.check_all(box, user_id)
    return str(user_id)
    pass

async def simple(event):
    time.sleep(0.5)
    print('here')
    t = time.perf_counter()
    box = DataBox(event)
    await co.check_all(box, box.msg.from_id)
    print(time.perf_counter()-t)
    return "simple"
    pass

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
