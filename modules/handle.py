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
    PayloadFilter,
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
    ban,
    system,
    chatstatuses,
)

command_dict = {
    'kick' : {'obj' : kick.kick_for_handle, 'level' : 1},
    'broadcast' : {'obj' : broadcast.broadcast, 'level' : 1},
    't' : {'obj' : test.test, 'level' : 1},
    'op' : {'obj' : chatcontrol.add_admin, 'level' : 1},
    'deop' : {'obj' : chatcontrol.del_admin, 'level' : 1},
    'addchat' : {'obj' : chatcontrol.add_chat, 'level' : 1},
    'delchat' : {'obj' : chatcontrol.del_chat, 'level' : 1},
    'addgroup' : {'obj' : chatcontrol.add_group, 'level' : 1},
    'delgroup' : {'obj' : chatcontrol.del_group, 'level' : 1},
    'addchattogroup' : {'obj' : chatcontrol.add_chat_to_group, 'level' : 1},
    'delchatfromgroup' : {'obj' : chatcontrol.del_chat_from_group, 'level' : 1},
    'addadmintochat' : {'obj' : chatcontrol.add_admin_to_chat, 'level' : 1},
    'deladminfromchat' : {'obj' : chatcontrol.del_admin_from_chat, 'level' : 1},
    'ban' : {'obj' : ban.add_ban, 'level' : 1},
    'forgive' : {'obj' : ban.del_ban, 'level' : 1},
    'permban' : {'obj' : ban.add_perm_ban, 'level' : 1},
    'delpermban' : {'obj' : ban.del_perm_ban, 'level' : 1},
    'uptime' : {'obj' : system.uptime, 'level' : 1},
    'stop' : {'obj' : system.stop, 'level' : 1},
    'log' : {'obj' : system.log, 'level' : 1},
    'clearlog' : {'obj' : system.clear_log, 'level' : 1},
    'basedump' : {'obj' : system.base_dump, 'level' : 1},
    'mute' : {'obj' : chatstatuses.add_mute, 'level' : 1},
    'unmute' : {'obj' : chatstatuses.del_mute, 'level' : 1},
    'closegate' : {'obj' : chatstatuses.add_gate, 'level' : 1},
    'opengate' : {'obj' : chatstatuses.del_gate, 'level' : 1},
    'chatstatus' : {'obj' : chatstatuses.get_chat_statuses, 'level' : 1}

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
                if box.admin_level <= 2:
                    box.targets = await base.handle_targets(box.targets) # create this handle func!
                await command_dict[box.command]['obj'](box)
            except Exception as e:
                raise SystemExit(e)
    if box.admin_level == 0:
        await simple(event)

async def keyboard(event):
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
            EventTypeFilter('message_new') & # without callback button support!
            PayloadFilter(None)
        )
        .handle(command)
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
