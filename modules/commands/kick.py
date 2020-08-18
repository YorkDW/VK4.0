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
    kick_users = []
    kick_chats = []
    res = []
    for user in users:
        for peer in peers:
            kick_users.append(user)
            kick_chats.append(peer-2000000000)
            if len(kick_users) == 25:
                res += (await kick_them(api=api, chats=kick_chats, users=kick_users)).response
                kick_users = []
                kick_chats = []
    if len(kick_users)>0:
        res += (await kick_them(api=api, chats=kick_chats, users=kick_users)).response
    return res

@log_and_respond_decorator
async def kick(box):
    admin = box.msg.from_id
    for target in await box.targets:
        target_level = base.get_admin_level(target)
        protected = any([
            target_level >= 2, 
            target_level >= base.get_admin_level(admin) if admin != 'auto' else False,
            target == admin
        ])
        if protected:
            box.remove_target(target)
    errors = check_zeros({"target":await box.targets, "chat":box.chats})
    if errors:
        return (False, errors, errors)
    res = await execute_kicks(box.api, box.chats, await box.targets)

    return (True, f"kicked {await box.targets}, {stat}", f"result {get_stat(res)}")