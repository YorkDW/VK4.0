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
    talker,
    keyboard,
    config,
    chattools,
)

command_dict = {
    'kick' : {'obj' : kick.kick_for_handle, 'level' : 1},
    'broadcast' : {'obj' : broadcast.broadcast, 'level' : 3},
    'op' : {'obj' : chatcontrol.add_admin, 'level' : 4},
    'deop' : {'obj' : chatcontrol.del_admin, 'level' : 4},
    'addchat' : {'obj' : chatcontrol.add_chat, 'level' : 3},
    'delchat' : {'obj' : chatcontrol.del_chat, 'level' : 3},
    'addgroup' : {'obj' : chatcontrol.add_group, 'level' : 3},
    'delgroup' : {'obj' : chatcontrol.del_group, 'level' : 3},
    'addchattogroup' : {'obj' : chatcontrol.add_chat_to_group, 'level' : 3},
    'delchatfromgroup' : {'obj' : chatcontrol.del_chat_from_group, 'level' : 3},
    'addadmin' : {'obj' : chatcontrol.add_admin_to_chat, 'level' : 3},
    'deladmin' : {'obj' : chatcontrol.del_admin_from_chat, 'level' : 3},
    'ban' : {'obj' : ban.add_ban, 'level' : 1},
    'forgive' : {'obj' : ban.del_ban, 'level' : 2},
    'permban' : {'obj' : ban.add_perm_ban, 'level' : 2},
    'delpermban' : {'obj' : ban.del_perm_ban, 'level' : 3},
    'uptime' : {'obj' : system.uptime, 'level' : 1},
    'stop' : {'obj' : system.stop, 'level' : 4},
    'log' : {'obj' : system.log, 'level' : 4},
    'clearlog' : {'obj' : system.clear_log, 'level' : 4},
    'mute' : {'obj' : chatstatuses.add_mute, 'level' : 2},
    'unmute' : {'obj' : chatstatuses.del_mute, 'level' : 2},
    'closegate' : {'obj' : chatstatuses.add_gate, 'level' : 2},
    'opengate' : {'obj' : chatstatuses.del_gate, 'level' : 2},
    'chatstatus' : {'obj' : chatstatuses.get_chat_statuses, 'level' : 1},
    'actt' : {'obj' : talker.activate_talker, 'level' : 3},
    'deactt' : {'obj' : talker.deactivate_talker, 'level' : 3},
    'setcatch' : {'obj' : config.set_enter_count, 'level' : 3},
    'settarget' : {'obj' : config.set_target_count, 'level' : 3},
    'targets' : {'obj' : config.get_target_count, 'level' : 1},
    'savebase' : {'obj' : system.base_save, 'level' : 4},
    'loadbase' : {'obj' : system.base_load, 'level' : 4},
    'chats' : {'obj' : chattools.aviable_chats, 'level' : 1},
    'loglevel' : {'obj' : system.log_level, 'level' : 4},
    'admins' : {'obj' : system.get_admins, 'level' : 3},
    'banlist' : {'obj' : system.get_banlist, 'level' : 3}
}



async def new_user(event):
    box = DataBox(event)
    if box.msg.action.type is MessagesMessageActionStatus.CHAT_INVITE_USER:
        user_id = box.msg.action.member_id
    elif box.msg.action.type is MessagesMessageActionStatus.CHAT_INVITE_USER_BY_LINK:
        user_id = box.msg.from_id
    await checkuser.check_all(box, user_id)

async def simple_msg(event):
    box = DataBox(event)
    if base.is_muted(box.msg.from_id, box.msg.peer_id):
        if not base.is_chat_admin(box.msg.from_id, box.msg.peer_id):
            await kick.execute_kicks(box.api, box.msg.peer_id, box.msg.from_id)

    if box.msg.peer_id > 2*10**9:
        if box.msg.peer_id not in stor.vault['chats'].keys():
            await log_respond(box, f"VOID in {box.msg.peer_id-2*10**9} from {box.msg.from_id} - {box.msg.text}")
    
    await talker.talker_handle(box)

async def command(event):
    box = DataBox(event)
    if box.command in command_dict.keys():
        if box.admin_level >= command_dict[box.command]['level']:
            try:
                if box.admin_level <= 2 and command_dict[box.command]['level'] > 0:
                    box.targets = await base.handle_targets(box.msg.from_id, box.targets, int(time.time())+stor.time_day)
                await command_dict[box.command]['obj'](box)
            except Exception as e:
                raise SystemExit(e)
    if box.admin_level == 0:
        await simple_msg(event)

async def keyboard_msg(event):
    box = DataBox(event)
    if not await keyboard.handle_keyboard(box):
        await simple_msg(event)



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
            EventTypeFilter('message_new') & (
            ChatActionFilter(MessagesMessageActionStatus.CHAT_INVITE_USER) |
            ChatActionFilter(MessagesMessageActionStatus.CHAT_INVITE_USER_BY_LINK)
            )
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
        .handle(keyboard_msg)
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
        .handle(simple_msg)
        .ready()
    )
    return router
