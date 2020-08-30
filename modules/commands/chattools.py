from modules.commands.utils import *

@log_and_respond_decorator
async def aviable_chats(box):
    extended_mode = False
    chat_ids = []

    if box.chats:
        chat_ids = box.chats
    elif box.admin_level >= 3:
        extended_mode = True
        chats_in_vault = list(stor.vault['chats'].keys())
        max_id = max(chats_in_vault)
        chat_ids = list(range(2*10**9+1, max_id+1))

    if not chat_ids:
        return (False, 'Wrong chats', 'Wrong chats')
    
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

    result = []
    for pack in respond:
        for chat in pack['items']:
            short_chat_id = chat['peer']['local_id']
            chat_id = chat['peer']['id']
            name = chat['chat_settings']['title']
            inner_name = foreign = ''
            if chat_id in stor.vault['chats'].keys():
                inner_name = f"({stor.vault['chats'][chat_id]['name']})"
            else:
                foreign = '!'
            
            result.append((foreign, short_chat_id, inner_name, name))

    for_send = '\n'.join(map(lambda pair: f"{pair[0]} {pair[1]} {pair[2]}: {pair[3]}", result))
    return (True, f"{len(result)} chats", for_send)
