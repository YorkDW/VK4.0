 
import random, time

from vkwave.api import APIOptionsRequestContext
from vkwave.bots import SimpleLongPollBot, TaskManager
from vkwave.vkscript import execute
from vkwave.types.responses import ExecuteResponse

import modules.storage as stor
import modules.basemaster as base
from modules.message import split_message_dict, get_message_resend_dict, send_new

class st:
    logger:None



async def send_message(api, send_args:dict):
    send_args.update({"random_id":random.randint(50000,2000000000)})
    await api.messages.send(**send_args)
    
async def send_answer(box, text):
    send_args = {"peer_id":box.msg.peer_id, "message":text}
    await send_message(box.api, send_args)

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

def get_stat(ex_res:list):
    errors = 0
    for elem in ex_res:
        if isinstance(elem, bool) and elem == False:
            errors += 1
    return f"{len(ex_res)-errors}/{len(ex_res)}"


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
    stat = get_stat(res)
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

async def get_call_list(api, chats):  
        call_ids = call_list = {}
        for_execue = []

        for peer in chats:
            call_ids.update({peer:[]})
            for_execue.append(('messages.getConversationMembers',{"peer_id":peer}))

        res_execue = await stor.execue(api, for_execue)

        for chat_num, members_object in enumerate(res_execue):
            if not members_object:
                continue
            for member in members_object['items']:
                if member['member_id']>0 and not base.is_chat_admin(member['member_id'], chats[chat_num]):
                    call_ids[chats[chat_num]].append(member['member_id'])

        for peer, ids in call_ids.items():
            ids = list(map(lambda peer:f"[id{peer}|-]", ids))
            text = ""
            for i in range(0, len(ids), 25):
                text += '\n' + ''.join(ids[i:i+25])
            call_list.update({peer: text})

        return call_list

async def broadcast(box):
    if box.msg.reply_message:
        for_send = await get_message_resend_dict(box.api, box.msg.reply_message)
    elif box.msg.fwd_messages:
        for_send = await get_message_resend_dict(box.api, box.msg.fwd_messages)
    elif '\n' in box.msg.text:
        for_send = await get_message_resend_dict(box.api, box.msg)
        for_send["message"] = for_send["message"][for_send["message"].find("\n")+1:]
    elif box.msg.attachments:
        for_send = await get_message_resend_dict(box.api, box.msg)
        for_send["message"] = ""
    else:
        return False # bad end
    call_list = await get_call_list(box.api, box.chats) if box.param == "call" else {}
    for_execue = []

    for peer in box.chats:
        for_send_with_calls = for_send.copy()
        if peer in call_list.keys():
            for_send_with_calls["message"] += call_list[peer]
        msg_list = await split_message_dict(for_send_with_calls)
        for msg in msg_list:
            for_execue.append(("messages.send",msg))
            for_execue[-1][1].update({"peer_id":peer, "random_id":random.randint(50000,2000000000)})
    res = await stor.execue(box.api, for_execue)

    print(get_stat(res))
    
    

    





async def test(box):
    msgs = [box.msg]
    if box.msg.fwd_messages:
        msgs += box.msg.fwd_messages
    elif box.msg.reply_message:
        msgs.append(box.msg.reply_message)

    for_send = await get_message_resend_dict(box.api, msgs)
    await get_call_list(box)
    # print(await send_new(box.api, for_send, box.msg.peer_id))

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
