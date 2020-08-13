 
import random, time

from vkwave.api import APIOptionsRequestContext
from vkwave.bots import SimpleLongPollBot, TaskManager
from vkwave.vkscript import execute
from vkwave.types.responses import ExecuteResponse

import modules.storage as stor
import modules.basemaster as base

class st:
    logger:None



#update for attachmets later
async def send_text(api, peer, text):
    await api.messages.send(
        random_id=random.randint(50000,2000000000),
        peer_id = peer,
        message = text
    )
    
async def send_answer(box, text):
    await send_text(box.api, box.msg.peer_id, text)

async def log_respond(box, log, answer = False,level=12):
    st.logger.log(level, f" {log}")
    if answer:
        await send_answer(box, answer)

def log_and_respond_decorator(func):
    async def body(*args, **kwargs):
        status, log, answer = await func(*args, **kwargs)

        intro = 'Done:' if status else 'FAIL:'
        level = 12 if status else 14
        log_for_send = f"{intro} {func.__name__}{args}{kwargs} - {log}"

        if len(args)>0 and isinstance(args[0],base.DataBox):
            await log_respond(args[0], log_for_send, answer, level)
        else:
            print('ERROR')
            raise SystemExit
        return (status, log, answer)
    return body

def check_zeros(name_and_val):
    res = []
    for key, value in name_and_val.items():
        if not value:
            res.append(f"Wrong {key}")
    return False if not res else ', '.join(res)


@execute
def kick_them(api: APIOptionsRequestContext, chats: list, users: list):
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
    stat = f"{res.count(True)}/{len(res)}"
    return (True, f"kicked {await box.targets}, {stat}", f"result - {stat}")


async def check_ban(box, user_id):
    if base.is_banned(user_id, box.msg.peer_id):
        await log_respond(box, f"Ban triggered at {box.msg.peer_id} by {user_id}")
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return True
    return False

async def catch_runner(box, user_id):
    enters = await base.handle_enter(user_id, box.msg.peer_id, int(time.time()))
    count_of_enters = len(enters)
    if count_of_enters == stor.config['MAXENTERS']:
        await send_answer(box, "You will be kicked for any enterance in 24 hours")
    if count_of_enters > stor.config['MAXENTERS']:
        print(enters)
        await log_respond(box, f"Runner {user_id} was caught at {box.peer_id-2000000000}")
        # await execute_kicks(box.api, enters, user_id)
        return True
    return False
    
async def undesirable (box, user_id):
    if user_id<0 and user_id != box.event.group_id:
        await log_respond(box, f"Bot was caught at {box.msg.peer_id}", "I am the only bot here")
        await execute_kicks(box.api, box.msg.peer_id, user_id)
    if base.check_gate(box.msg.peer_id):
        await log_respond(box, f"{user_id} kicked by closed gates at {box.msg.peer_id}")
        await execute_kicks(box.api, box.msg.peer_id, user_id)

async def check_all(box, user_id):
    if not verify_chat(chat_id):
        return
    if await check_ban(box, user_id):
        return
    if base.is_chat_admin(user_id, box.msg.peer_id):
        pass
        #return
    if await catch_runner(box, user_id):
        return
    await undesirable(box, user_id)


async def test_all():
    chat_id = 567
    admin_id = 1234
    t = time.perf_counter()
    await base.add_group('testtt')
    await base.add_chat(chat_id, 'chat_name')
    await base.add_chat_to_group(chat_id, 'testtt')
    await base.add_admin(admin_id,3,'admin_name')
    await base.add_admin_to_chat(chat_id,admin_id)
    await base.add_gate(chat_id, time.time()+10)
    await base.add_mute(chat_id, 333, time.time()+10)
    await base.update_vault_all()
    stor.dump(stor.vault)
    await base.del_gate(chat_id)
    await base.del_mute(chat_id, 333)
    await base.add_target(admin_id,333,time.time()+10)
    await base.del_admin(admin_id)
    await base.del_chat(chat_id)
    await base.del_group('testtt')
    await base.update_vault_all()
    print(stor.vault)
    print(time.perf_counter()-t)
