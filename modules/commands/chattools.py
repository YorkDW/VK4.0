from modules.commands.utils import *


async def get_chats(box, chat_ids, extended_mode, max_id=0):
    chat_ids_by_100 = [chat_ids[i:i+100] for i in range(0,len(chat_ids),100)]

    for_execue = []
    for block_100 in chat_ids_by_100:
        for_execue.append(('messages.getConversationsById',{'peer_ids':block_100}))
    respond = await stor.execue(box.api, for_execue)

    while extended_mode:
        max_id = max_id+1
        try:
            last_chat = await box.api.messages.get_conversations_by_id(
                peer_ids=[max_id],
                return_raw_response = True
                )
            last_chat = last_chat['response']
            respond.append(last_chat)
        except:
            break

    chat_list = [chat for pack in respond for chat in pack['items']]

    return chat_list

@log_and_respond_decorator
async def aviable_chats(box):
    extended_mode = False
    chat_ids = []
    max_id = 0

    if box.chats:
        chat_ids = box.chats
    elif box.admin_level >= 3:
        extended_mode = True
        chats_in_vault = list(stor.vault['chats'].keys())
        max_id = max(chats_in_vault)
        chat_ids = list(range(2*10**9+1, max_id+1))

    if not chat_ids:
        return (False, 'Wrong chats', 'Wrong chats')
    
    chat_list = await get_chats(box, chat_ids, extended_mode, max_id)

    result = []

    for chat in chat_list:
        short_chat_id = chat['peer']['local_id']
        chat_id = chat['peer']['id']
        name = chat['chat_settings']['title']
        inner_name = foreign = ''
        can_moderate = '' if chat['chat_settings']['acl']['can_moderate'] else "NO RIGHTS"
        if chat_id in stor.vault['chats'].keys():
            inner_name = f"({stor.vault['chats'][chat_id]['name']})"
        else:
            foreign = '!'

        res_str = f"{foreign} {short_chat_id} {inner_name}: {name} {can_moderate}"
        
        result.append(res_str)

    for_send = '\n'.join(result)
    return (True, f"{len(result)} chats", for_send)



# доделать, выборка по чатам
@log_and_respond_decorator
async def search(box):
    try:
        rows = [ row.split(' ') for row in box.msg.text.lower().split('\n')[1:] ]
        name_dict = {row[0] : tuple(row[1:]) for row in rows}

    except:
        name_dict = {}

    finally:
        if not name_dict:
            return (False, 'Wrong names', 'Wrong names')
    
    await send_answer(box, 'Searching...')

    chats = list(stor.vault['chats'].keys())

    for_execue = [('messages.getConversationMembers', {'peer_id':chat}) for chat in chats]
    get_members_result = await stor.execue(box.api, for_execue)

    check_in = lambda items: [prof['member_id'] for prof in items]


    result = {}
    for i, chat in enumerate(chats):
        if not get_members_result[i]:
            continue

        profiles = get_members_result[i]['profiles']
        check = check_in(get_members_result[i]['items'])
        
        for prof in profiles:
            if not is_wanted(prof, name_dict):
                continue

            key = f"[id{prof['id']}|{prof['last_name']} {prof['first_name']}]"

            if key not in result.keys():
                result[key] = ['--|--']

            if prof['id'] in check:
                result[key].insert(0, stor.vault['chats'][chat]['name'])
            else:
                result[key].append(stor.vault['chats'][chat]['name'])
        
    if len(result) > 0:
        text = '\n'.join([f"{key}: {', '.join(value)}" for key, value in result.items()])
    else:
        text = ''
    
    return (True, f"{len(result)} results finded", f"{len(result)} results finded\n{text}")


def is_wanted(prof, name_dict):
    first = prof['first_name'].lower()
    last = prof['last_name'].lower()

    if last in name_dict.keys():
        if first in name_dict[last] or '%' in name_dict[last]:
            return True

    if '%' in name_dict.keys():
        if first in name_dict['%'] or '%' in name_dict['%']:
            return True

    return False