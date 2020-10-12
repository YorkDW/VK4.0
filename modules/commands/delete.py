from modules.commands.utils import *
from modules.commands.chattools import get_chats

# class SpecialDataBox(DataBox):

#     def __init__(self, api):
#         self.user_api = api

#     @property
#     def api(self):
#         return self.user_api.get_context()


# async def transform_peer_ids_getter(box, peer_ids):
#     user_box = SpecialDataBox(stor.user_api)
#     ids = list(range(2000000001,2000000138))
#     user_chats = await get_chats(user_box, ids, False)
#     bot_chats = await get_chats(box, list(stor.vault['chats'].keys()), False)

#     trans_tab = {}
#     for b_chat in bot_chats:
#         for u_chat in user_chats:
#             if u_chat['chat_settings']['title'] == b_chat['chat_settings']['title']:
#                 trans_tab[b_chat['peer']['id']] = u_chat['peer']['id']
#     print(trans_tab)
#     stor.dump(trans_tab)

#     return peer_ids

def transform_peer_ids(peer_ids):
    trans_dict = {1: 46, 2: 35, 3: 12, 77: 137, 4: 22,5: 15, 9: 16, 12: 40, 14: 5, 15: 39, 16: 45, 17: 18, 
    18: 19, 19: 20, 20: 41, 21: 21, 22: 47, 23: 48, 24: 49, 25: 50, 26: 51, 27: 52, 28: 53, 29: 54, 30: 55, 
    31: 56, 32: 57, 33: 58, 34: 59, 35: 60, 36: 61, 37: 62, 38: 63, 39: 64, 40: 65, 41: 66, 42: 67, 
    43: 68, 44: 69, 45: 70, 46: 71, 47: 72, 48: 73, 49: 74, 50: 75, 51: 76, 53: 24, 55: 36, 56: 14, 
    57: 10, 59: 44, 60: 42, 61: 38, 62: 34, 63: 43, 64: 11, 65: 4, 66: 37, 67: 17, 68: 13, 69: 8, 
    70: 7, 71: 6, 72: 3, 73: 2, 74: 1, 75: 9, 81: 107, 82: 108, 83: 109, 84: 110, 85: 111, 86: 113, 
    87: 112, 88: 114, 89: 115, 90: 116, 91: 117, 92: 118, 93: 119, 94: 120, 95: 121, 96: 122, 97: 123, 
    98: 124, 99: 125, 100: 126, 101: 127, 102: 128, 103: 129, 104: 130, 105: 131, 106: 132, 107: 133, 
    108: 134, 109: 135, 110: 136}
    # 5: 15, 6: 30, 7: 29, 8: 28, 10: 27, 11: 26, 13: 25, 58: 23, 18: 19,
    return [trans_dict[peer-2*10**9]+2*10**9 for peer in peer_ids if peer-2*10**9 in trans_dict.keys()]

# create autogenerate for user peer ids 

async def delete_msgs_by_ids(msg_ids, cur_step=0):
    STEPS = (100, 4, 1)
    msg_ids_by_step = [msg_ids[i:i+STEPS[cur_step]] for i in range(0, len(msg_ids), STEPS[cur_step])]
    for_execue = [('messages.delete', {"message_ids":block, "delete_for_all":1}) for block in msg_ids_by_step]
    res = await stor.execue(stor.user_api.get_context(), for_execue)

    ids_with_error = []
    for num, status in enumerate(res):
        if not status:
            ids_with_error.extend(msg_ids_by_step[num])
    
    if not ids_with_error or cur_step == len(STEPS)-1:
        return ids_with_error

    return await delete_msgs_by_ids(ids_with_error, cur_step+1)    

def type_check(msg, attach_type):
    return any([att.type==attach_type for att in msg.attachments])

def text_check(msg, text):
    return text in msg.text

def from_user_check(msg, user_ids:list):
    return msg.from_id in user_ids

def deep_check_msg(msg, check_func, value):
    return any([
        (deep_check_msg(msg.reply_message, check_func, value) if msg.reply_message else False),
        ([deep_check_msg(fwd_msg, check_func, value) for fwd_msg in msg.fwd_messages] if msg.fwd_messages else []),
        check_func(msg, value)
        ])

def filter_msgs(msgs, params:dict):
    if params['check_type'] and not params['check_func']:
        params['check_func'] = globals()[f"{params['check_type']}_check"]

    

    result = []
    overflow = False

    for num, msg in enumerate(msgs):
        if any([
            params['count'] and params['count'] < num + 1,
            params['timestamp'] and params['timestamp'] > msg.date,
            params['conv_msg_id'] and params['conv_msg_id'] >= msg.conversation_message_id
            ]):
                overflow = True
                continue

        if any([
            msg.action,
            params['peer_ids'] and msg.peer_id not in params['peer_ids'],
            params['untouchable'] and msg.from_id in params['untouchable'],
            params['user_ids'] and not deep_check_msg(msg, from_user_check, params['user_ids']),
            params['check_value'] and not deep_check_msg(msg, params['check_func'], params['check_value'])
            ]):
                continue

        result.append(msg.id)

    return (result, overflow)

async def find_by(params:dict): # with search method
    if params['check_type'] == 'text':
        text_for_find = params['check_value']
    elif params['check_type'] == 'from_user':
        user_data = (await stor.user_api.get_context().users.get(user_ids=params['check_value'][0])).response[0] # one user only 
        text_for_find = f"{user_data.last_name} {user_data.first_name}"
    else:
        raise Exception('Wrong check_type in find_by method')
    
    result = []
    overflow = False
    offset = 0
    while not overflow:
        try:
            msgs = (await stor.user_api.get_context()
                .messages.search(q=text_for_find, count=100, offset=offset)).response.items
        except:
            break

        if not msgs:
            break

        filtered_msg_ids, overflow = filter_msgs(msgs, params)
        result.extend(filtered_msg_ids)
        offset += 100
    
    return result

async def find_from(params:dict): # with getHistory method
    params = params.copy()
    if 'untouchable' not in params.keys() or not params['untouchable']:
        chat_members = (await stor.user_api.get_context().messages.get_conversation_members(peer_id=params['peer_ids'][0]))
        chat_members = chat_members.response.items
        params['untouchable'] = [user.member_id for user in chat_members if user.is_admin]
    
    result = []
    overflow = False
    offset = 0
    while not overflow:
        try:
            msgs = (await stor.user_api.get_context().messages.get_history(peer_id=params['peer_ids'][0], offset=offset, count=200)).response.items
        except:
            break

        if not msgs:
            break

        filtered_msg_ids, overflow = filter_msgs(msgs, params)
        result.extend(filtered_msg_ids)
        offset += 200
    
    return result

def get_first_fwd(box):
    if box.msg.fwd_messages:
        return box.msg.fwd_messages[0]
    if box.msg.reply_message:
        return box.msg.reply_message
    return None

def get_basic_params():
    default_params = ('conv_msg_id', 'user_ids', 'count', 
    'untouchable', 'check_type', 'check_value', 'check_func', 'timestamp')

    params = dict()

    for param_name in default_params:
        params[param_name] = None

    day_ago = int(time.time()-stor.time_day)
    params['timestamp'] = day_ago
    return params

def fill_common_params(box, params):
    params['peer_ids'] = transform_peer_ids(box.chats) or None

    if not params['peer_ids']:
        return (False, "Wrong chats", "Wrong chats")

    param_from = box.get_by_name("from")
    param_time = box.get_by_name("time")
    
    if param_from:
        params['user_ids'] = box.targets
        if not params['user_ids']:
            return (False, "Wrong targets", "Wrong targets")

    if param_time:
        seconds = str_to_sec(param_time)
        time_ = int(time.time() - seconds) if seconds else False

        if time_  and time_ >= params['timestamp']:
            params['timestamp'] = time_
        else:
            return (False, "Wrong time", "Wrong time")

    return params

@log_and_respond_decorator
async def delete_message(box):
    params = fill_common_params(box, get_basic_params())
    if isinstance(params, tuple):
        return params
    params['untouchable'] = [box.event.object.group_id*-1] + list(stor.vault['admins'].keys())
    param_by = box.get_by_name("by")
    param_text = box.get_by_name("text")

    if param_text:
        params['check_type'] = 'text'
        params['check_value'] = param_text
        
    elif param_by == 'text':
        fwd = get_first_fwd(box)
        if not fwd:
            return (False, "Wrong text", "Wrong text")
        params['check_type'] = 'text'
        params['check_value'] = fwd.text

    elif param_by == 'user':
        if not box.targets:
            return (False, "Wrong target", "Wrong target")
        if len(box.targets) > 1:
            return (False, "Only 1 target is needed", "Only 1 target is needed")

        params['check_type'] = 'from_user'
        params['check_value'] = box.targets
            

    else:
        return (False, 'Use "text" or "by"', 'Use "text" or "by"')

    msg_ids = await find_by(params)

    if not msg_ids:
        return (False, "Can't find messages", "Can't find messages")

    errors = await delete_msgs_by_ids(msg_ids)

    stat = f"{len(msg_ids)-len(errors)}/{len(msg_ids)} messages deleted"
    return (True, stat, stat)
    
@log_and_respond_decorator
async def clean_conversation(box):
    params = fill_common_params(box, get_basic_params())
    if isinstance(params, tuple):
        return params

    param_count = box.get_by_name("count")
    param_type = box.get_by_name("type")
    param_till = box.get_by_name("till")

    if param_count:
        if not param_count.isdigit():
            return (False, "Wrong count", "Wrong count")
        params['count'] = int(param_count)

    if param_type:
        params['check_type'] = 'type'
        params['check_value'] = param_type

    if param_till:
        fwd = get_first_fwd(box)
        if not fwd:
            return (False, "Wrong message", "Wrong message")
        params['conv_msg_id'] = fwd.conversation_message_id

    if not params['peer_ids'] or len(params['peer_ids']) != 1:
        return (False, "Not only one peer_id", "Choose only one chat")

    if not set(['timestamp', 'conv_msg_id', 'user_ids', 'count']).intersection(set(params.keys())):
        return (False, "Use any params", "Use any params")

    msg_ids = await find_from(params)

    errors = await delete_msgs_by_ids(msg_ids)

    stat = f"{len(msg_ids)-len(errors)}/{len(msg_ids)} messages deleted"
    return (True, stat, stat)