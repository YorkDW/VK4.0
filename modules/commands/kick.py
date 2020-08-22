from vkwave.vkscript import execute
from modules.commands.utils import *



@execute
def kick_them(api, chats: list, users: list):
    i=0
    res = []
    while i<len(users):
        res.append(api.messages.removeChatUser(
            chat_id=chats[i],
            user_id=users[i]))
        i+=1
    return res

async def execute_kicks(api, peers, users):
    if not isinstance(peers, (list, tuple)):
        peers = [peers]
    if not isinstance(users, (list, tuple)):
        users = [users]
    for_execue = []
    for user in users:
        for peer in peers:
            for_execue.append(
                ('messages.removeChatUser', {'chat_id':peer-2000000000, 'user_id':user})
                )
    return await stor.execue(api, for_execue)

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
    res = await execute_kicks(box.api, box.chats, box.targets)

    return (True, f"kicked {box.targets}, {get_stat(res)}", f"result {get_stat(res)}")

@log_and_respond_decorator
async def kick_for_handle(box):
    return await kick(box)