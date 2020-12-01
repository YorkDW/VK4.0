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
from modules.commands.utils import *
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
    delete,
)

@log_and_respond_decorator
async def do_as_someone(box): # just cause
    target = box.get_id_from_word(box.text_list(2))
    if not target:
        return (False, 'Wrong target', 'Wrong target')

    new_text = ' '.join(box.text_list()[0:1] + box.text_list()[3:])
    old_from_id = box.event.object.object.message.from_id

    box.event.object.object.message.text = new_text
    box.event.object.object.message.from_id = target

    await command(box.event)
    box.event.object.object.message.from_id = old_from_id

    return (True, f"Done as {target}", f"Done as [id{target}|*id{target}]")

@log_and_respond_decorator
async def do_from_somewhere(box): # just cause
    if len(box.chats) > 1:
        return (False, 'Only one chat needed', 'Only one chat needed')

    if box.chats:
        target = box.chats[0]
    else:
        target = box.get_id_from_word(box.text_list(2))

    if not target:
        return (False, 'Wrong chat', 'Wrong chat')

    new_text = ' '.join(box.text_list()[0:1] + box.text_list()[3:])
    old_peer_id = box.event.object.object.message.peer_id

    box.event.object.object.message.peer_id = target
    box.event.object.object.message.text = new_text

    await command(box.event)
    box.event.object.object.message.peer_id = old_peer_id

    return (True, f"Done from {target}", f"Done from {target}")

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
    'loglevel' : {'obj' : config.log_level, 'level' : 4},
    'admins' : {'obj' : system.get_admins, 'level' : 3},
    'banlist' : {'obj' : system.get_banlist, 'level' : 3},
    'as' : {'obj' : do_as_someone, 'level' : 4},
    'from' : {'obj' : do_from_somewhere, 'level' : 4},
    'delete' : {'obj' : delete.delete_message, 'level' : 4},
    'clear' : {'obj' : delete.clean_conversation, 'level' : 4},
    's' : {'obj' : chattools.search, 'level' : 4}

}


async def test(event):
    box = DataBox(event)


async def new_user(event):
    box = DataBox(event)
    if box.msg.action.type is MessagesMessageActionStatus.CHAT_INVITE_USER\
        or box.msg.action.type is MessagesMessageActionStatus.CHAT_INVITE_USER_BY_MESSAGE_REQUEST:
        user_id = box.msg.action.member_id
    elif box.msg.action.type is MessagesMessageActionStatus.CHAT_INVITE_USER_BY_LINK:
        user_id = box.msg.from_id
    await checkuser.check_all(box, user_id)

async def simple_msg(event):
    box = DataBox(event)
    if base.is_muted(box.msg.from_id, box.msg.peer_id):
        if not base.is_chat_admin(box.msg.from_id, box.msg.peer_id):
            await kick.initiate_kicks(box.api, box.msg.peer_id, box.msg.from_id, msg_del=True)

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
    # router.registrar.register(
    #     router.registrar.new()
    #     .handle(test)
    #     .ready()
    # )

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
