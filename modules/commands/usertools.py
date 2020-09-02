from modules.commands.utils import *

def transform_peer_ids(peer_ids):
    print("TODO Transfer")
    return peer_ids

async def deleter(msg_ids):
    msg_ids_by_100 = [msg_ids[i:i+100] for i in range(0,len(msg_ids),100)]
    for_execue = []
    for block in msg_ids_by_100:
        for_execue.append(('messages.delete', {"message_ids":block, "delete_for_all":1}))
    res = await stor.execue(stor.user_api.get_context(), for_execue)
    return res
    
async def find_by_text(text, peer_ids=None, user_id=None):  # проверить поиск по имени пользователя
    msgs = (await stor.user_api.get_context().messages.search(q=text, count=100)).response
    result = []
    time_ = int(time.time()-stor.time_day)

    for msg in msgs.items:
        if peer_ids and msg.peer_id not in peer_ids:
            continue
        if user_id and msg.from_id not in user_id:
            continue
        if msg.date > time_:
            result.append(msg.id)

    return result

async def find_by_user(api, user_id, peer_ids=None):
    user_data = (await api.users.get(user_ids=user_id)).response
    name_for_find = f"{user_data.last_name} {user_data.first_name}"
    return await find_by_text(name_for_find, peer_ids, user_id)

def extract_messages(msgs, till_timestamp=None, till_conv_msg_id=None, user_ids=None, count=None):
    result = []
    cur_count = 0
    for msg in msgs:
        if count and count < cur_count:
            break
        if till_timestamp and msg.date<till_timestamp:
            break
        if till_conv_msg_id and msg.conversation_message_id<till_conv_msg_id:
            break
        if user_id and msg.from_id in user_ids:
            continue

        result.append(msg.id)
    else:
        return (True, result)
    return (False, result)
        


async def find_from_conversation(peer_id, till_timestamp=None, till_conv_msg_id=None, user_ids=None, count=None):
    cur_offset = 0
    status = True
    msg_ids = []
    day_ago = time.time()-stor.time_day
    till_timestamp = till_timestamp if till_timestamp and till_timestamp > day_ago else day_ago

    while status:
        msgs = stor.user_api.get_context().messages.get_history(peer_id=peer_id, offset=cur_offset, count=200)
        cur_offset += 200
        status, temp_msg_ids = extract_messages(msgs, till_timestamp, till_conv_msg_id, user_ids, count)
        msg_ids.extend(temp_msg_ids)
    
    return msg_ids

def get_first_fwd(box):
    if box.msg.fwd_messages:
        return box.msg.fwd_messages[0]
    if box.msg.reply_message:
        return box.msg.reply_message
    return None


@log_and_respond_decorator
async def delete_message(box):
    peer_ids = transform_peer_ids(box.chats)


    param_by = box.get_by_name("by")
    param_text = box.get_by_name("text")
    
    if param_text:
        msg_ids = await find_by_text(param_text, peer_ids)

    elif param_by == 'text':
        fwd = get_first_fwd(box)
        if not fwd:
            return (False, "Wrong text", "Wrong text")
        msg_ids = await find_by_text(fwd.text, peer_ids)

    elif param_by == 'user':
        if not box.targets:
            return (False, "Wrong target", "Wrong target")
        msg_ids = await find_by_user(box.api, box.targets[0], peer_ids)

    else:
        return (False, "Wrong param", "Wrong param")
    
    if not msg_ids:
        return (False, "Can't find messages", "Can't find messages")

    res = await deleter(msg_ids)
    full_success = all(res)
    answer = "Messages fully deleted" if all(res) else "Messages partly deleted"

    return (True, answer, answer)


@log_and_respond_decorator
def clean_conversation(box):
    if len(box.chats) != 1:
        return (False, "One chat, please", "One chat, please")
    
    target_peer_id = transform_peer_ids(box.chats)[0]

    param_time = box.get_by_name("time")
    param_count = box.get_by_name("count")
    
    till_timestamp = None
    if param_time:
        time_ = str_to_sec(param_time)
        if not time_:
            return (False, "Wrong time", "Wrong time")
        till_timestamp = time_

    user_ids = None
    if box.get_by_name("user"):
        if not box.targets:
            return (False, "Wrong targets", "Wrong targets")
        user_ids = box.targets

    till_conv_msg_id = None
    if box.get_by_name("till"):
        fwd = get_first_fwd(box)
        if not fwd:
            return (False, "Wrong message", "Wrong message")
        till_conv_msg_id = fwd.conversation_message_id

    count = None
    if param_count:
        if not param_count.isdigit():
            return (False, "Wrong count", "Wrong count")
        count = int(param_count)
        
    msg_ids = await find_from_conversation(peer_id, till_timestamp, till_conv_msg_id, user_ids, count)

    if not msg_ids:
        return (False, "Can't find messages", "Can't find messages")

    res = await deleter(msg_ids)
    full_success = all(res)
    answer = "Messages fully deleted" if all(res) else "Messages partly deleted"

    return (True, answer, answer)

    # add delete photos
