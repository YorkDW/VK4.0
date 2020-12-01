from vkwave.vkscript import execute
from modules.commands.utils import *
from modules.commands.delete import prolonged_delete


async def execute_kicks(api, peers, users):
    for_execue = []
    for user in users:
        for peer in peers:
            for_execue.append(
                ('messages.removeChatUser', {'chat_id':peer-2000000000, 'member_id':user})
                )
    return await stor.execue(api, for_execue)

async def initiate_kicks(api, peers, users, msg_del=False):
    if not isinstance(peers, (list, tuple)):
        peers = [peers]
    if not isinstance(users, (list, tuple)):
        users = [users]

    if msg_del:
        for user in users:
            stor.do(prolonged_delete(user, peers))

    return await execute_kicks(api, peers, users)

def remove_protected_targets(box):
    admin = box.msg.from_id
    for target in box.targets:
        target_level = base.get_admin_level(target)
        protected = any([
            target_level >= 2, 
            target_level >= base.get_admin_level(admin),
            target == admin
            ])
        if protected:
            box.remove_target(target)

async def kick(box):
    remove_protected_targets(box)
    errors = check_zeros({"target":box.targets, "chat":box.chats})
    if errors:
        return (False, errors, errors)

    msg_del_flag = bool(box.get_by_name('delete'))

    res = await initiate_kicks(box.api, box.chats, box.targets, msg_del=msg_del_flag)

    return (True, f"kicked {box.targets}, {get_stat(res)}", f"result {get_stat(res)}")

@log_and_respond_decorator
async def kick_for_handle(box):
    return await kick(box)