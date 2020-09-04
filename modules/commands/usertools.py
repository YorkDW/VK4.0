from modules.commands.utils import *
from modules.commands.chattools import get_chats

class SpecialDataBox(DataBox):

    def __init__(self, api):
        self.user_api = api

    @property
    def api(self):
        return self.user_api.get_context()


async def transform_peer_ids_getter(box, peer_ids):
    user_box = SpecialDataBox(stor.user_api)
    ids = list(range(2000000001,2000000138))
    user_chats = await get_chats(user_box, ids, False)
    bot_chats = await get_chats(box, list(stor.vault['chats'].keys()), False)

    trans_tab = {}
    for b_chat in bot_chats:
        for u_chat in user_chats:
            if u_chat['chat_settings']['title'] == b_chat['chat_settings']['title']:
                trans_tab[b_chat['peer']['id']] = u_chat['peer']['id']
    print(trans_tab)
    stor.dump(trans_tab)

    return peer_ids

def transform_peer_ids(peer_ids):
    trans_dict = {2000000001: 2000000046, 2000000002: 2000000035, 2000000003: 2000000012, 2000000077: 2000000137,
    2000000004: 2000000022, 2000000005: 2000000015, 2000000006: 2000000030, 2000000007: 2000000029, 
    2000000008: 2000000028, 2000000009: 2000000016, 2000000010: 2000000027, 2000000011: 2000000026, 
    2000000012: 2000000040, 2000000013: 2000000025, 2000000014: 2000000005, 2000000015: 2000000039, 
    2000000016: 2000000045, 2000000017: 2000000018, 2000000018: 2000000019, 2000000019: 2000000020, 
    2000000020: 2000000041, 2000000021: 2000000021, 2000000022: 2000000047, 2000000023: 2000000048, 
    2000000024: 2000000049, 2000000025: 2000000050, 2000000026: 2000000051, 2000000027: 2000000052, 
    2000000028: 2000000053, 2000000029: 2000000054, 2000000030: 2000000055, 2000000031: 2000000056, 
    2000000032: 2000000057, 2000000033: 2000000058, 2000000034: 2000000059, 2000000035: 2000000060, 
    2000000036: 2000000061, 2000000037: 2000000062, 2000000038: 2000000063, 2000000039: 2000000064, 
    2000000040: 2000000065, 2000000041: 2000000066, 2000000042: 2000000067, 2000000043: 2000000068, 
    2000000044: 2000000069, 2000000045: 2000000070, 2000000046: 2000000071, 2000000047: 2000000072, 
    2000000048: 2000000073, 2000000049: 2000000074, 2000000050: 2000000075, 2000000051: 2000000076, 
    2000000053: 2000000024, 2000000055: 2000000036, 2000000056: 2000000014, 2000000057: 2000000010, 
    2000000058: 2000000023, 2000000059: 2000000044, 2000000060: 2000000042, 2000000061: 2000000038, 
    2000000062: 2000000034, 2000000063: 2000000043, 2000000064: 2000000011, 2000000065: 2000000004, 
    2000000066: 2000000037, 2000000067: 2000000017, 2000000068: 2000000013, 2000000069: 2000000008, 
    2000000070: 2000000007, 2000000071: 2000000006, 2000000072: 2000000003, 2000000073: 2000000002, 
    2000000074: 2000000001, 2000000075: 2000000009, 2000000081: 2000000107, 2000000082: 2000000108, 
    2000000083: 2000000109, 2000000084: 2000000110, 2000000085: 2000000111, 2000000086: 2000000113, 
    2000000087: 2000000112, 2000000088: 2000000114, 2000000089: 2000000115, 2000000090: 2000000116, 
    2000000091: 2000000117, 2000000092: 2000000118, 2000000093: 2000000119, 2000000094: 2000000120, 
    2000000095: 2000000121, 2000000096: 2000000122, 2000000097: 2000000123, 2000000098: 2000000124, 
    2000000099: 2000000125, 2000000100: 2000000126, 2000000101: 2000000127, 2000000102: 2000000128, 
    2000000103: 2000000129, 2000000104: 2000000130, 2000000105: 2000000131, 2000000106: 2000000132, 
    2000000107: 2000000133, 2000000108: 2000000134, 2000000109: 2000000135, 2000000110: 2000000136
    }
    return [trans_dict[peer] for peer in peer_ids if peer in trans_dict.keys()]

async def deleter(msg_ids):
    msg_ids_by_100 = [msg_ids[i:i+100] for i in range(0,len(msg_ids),100)]
    for_execue = []
    for block in msg_ids_by_100:
        for_execue.append(('messages.delete', {"message_ids":block, "delete_for_all":1}))
    res = await stor.execue(stor.user_api.get_context(), for_execue)
    return res
    
async def find_by_text(text, peer_ids=None, user_ids=None, untouchable=None):
    msgs = (await stor.user_api.get_context().messages.search(q=text, count=100)).response
    result = []
    time_ = int(time.time()-stor.time_day)

    for msg in msgs.items:
        if any([
            peer_ids and msg.peer_id not in peer_ids,
            user_ids and msg.from_id not in user_ids,
            untouchable and msg.from_id in untouchable
        ]):
            continue

        if msg.date > time_:
            result.append(msg.id)
    return result

async def find_by_user(api, user_id, peer_ids=None, untouchable=None):
    user_data = (await api.users.get(user_ids=user_id)).response
    name_for_find = f"{user_data.last_name} {user_data.first_name}"
    return await find_by_text(name_for_find, peer_ids, user_id)

def check_attach_type(msg, attach_type):
    return any(
        [check_attach_type(msg.reply_message, attach_type) if msg.reply_message else False] \
        + ([check_attach_type(fwd_msg, attach_type) for fwd_msg in msg.fwd_messages] if msg.fwd_messages else []) \
        + [att.type==attach_type for att in msg.attachments]
    )

def extract_msg_ids(msgs, till_timestamp=None, till_conv_msg_id=None, user_ids=None, count=None, untouchable=None, attach_type=None):
    result = []
    cur_count = 0
    for msg in msgs:
        cur_count +=1
        if any([
           count and count < cur_count,
           till_timestamp and msg.date<till_timestamp,
           till_conv_msg_id and msg.conversation_message_id<till_conv_msg_id
        ]):
            break

        if any([
           user_ids and msg.from_id not in user_ids,
           untouchable and msg.from_id in untouchable,
           msg.action,
           attach_type and not check_attach_type(msg, attach_type)
        ]):
            continue

        result.append(msg.id)
    else:
        return (True, result)
    return (False, result)
        


async def find_from_conversation(peer_id, till_timestamp=None, till_conv_msg_id=None,
                            user_ids=None, count=None, attach_type=None, untouchable=None):
    cur_offset = 0
    status = True
    msg_ids = []
    day_ago = time.time()-stor.time_day
    till_timestamp = till_timestamp if till_timestamp and till_timestamp > day_ago else day_ago
    if untouchable is None:
        chat_members = (await stor.user_api.get_context().messages.get_conversation_members(peer_id=peer_id)).response.items
        untouchable = [user.member_id for user in chat_members if user.is_admin]
    
    while status:
        msgs = (await stor.user_api.get_context().messages.get_history(peer_id=peer_id, offset=cur_offset, count=200)).response.items
        cur_offset += 200
        status, temp_msg_ids = extract_msg_ids(msgs, till_timestamp, till_conv_msg_id, user_ids, count, untouchable, attach_type)
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
    func_data = {
        "untouchable" : [box.event.object.group_id*-1] + list(stor.vault['admins'].keys())
    }

    if param_text:
        func_data.update({"func":find_by_text, "text":param_text, "peer_ids":peer_ids})

    elif param_by == 'text':
        fwd = get_first_fwd(box)
        if not fwd:
            return (False, "Wrong text", "Wrong text")
        func_data.update({"func":find_by_text, "text":fwd.text, "peer_ids":peer_ids})

    elif param_by == 'user':
        if not box.targets:
            return (False, "Wrong target", "Wrong target")
        func_data.update({"func":find_by_user, "user_id":box.targets[0], "peer_ids":peer_ids})

    else:
        return (False, "Wrong param", "Wrong param")
    
    msg_ids = await func_data.pop("func")(**func_data)

    if not msg_ids:
        return (False, "Can't find messages", "Can't find messages")

    res = await deleter(msg_ids)

    if all(res):
        return (True, "Messages deleted", "Messages deleted")
    else:
        return (False, "Error", "Error")


@log_and_respond_decorator
async def clean_conversation(box):
    if len(box.chats) > 0:
        return (False, "You can't choose chats", "You can't choose chats")
    
    user_chats = transform_peer_ids([box.msg.peer_id])
    if user_chats:
        peer_id = user_chats[0]
    else:
        return (False, "Iu is needed for deleter", "noiu")
    

    param_time = box.get_by_name("time")
    param_count = box.get_by_name("count")
    param_type = box.get_by_name("type")
    
    till_timestamp = None
    if param_time:
        time_ = str_to_sec(param_time)
        if not time_:
            return (False, "Wrong time", "Wrong time")
        till_timestamp = int(time.time()-time_)

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

    attach_type = None
    if param_type:
        attach_type = param_type
        
    if not any([till_timestamp, till_conv_msg_id, user_ids, count]):
        return (False, "Use any params", "Use any params")
    msg_ids = await find_from_conversation(peer_id, till_timestamp, till_conv_msg_id, user_ids, count, attach_type)

    if not msg_ids:
        return (False, "Can't find messages", "Can't find messages")

    res = await deleter(msg_ids)

    if all(res):
        return (True, "Messages deleted", "Messages deleted")
    else:
        return (False, "Error", "Error")

    # add finder for EU

    # we may add full admin check in delete_message
