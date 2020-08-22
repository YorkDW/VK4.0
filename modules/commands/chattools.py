from modules.commands.utils import *

@log_and_respond_decorator
async def all_chats(box):
    chats_in_vault = list(stor.vault['chats'].keys())
    max_id = max(chats_in_vault)
    chat_ids = list(range(2000000001, max_id+1))
    chat_ids_by_100 = [chat_ids[i:i+100] for i in range(0,len(chat_ids),100)]

    for_execue = []
    for block in chat_ids_by_100:
        for_execue.append(('messages.getConversationsById',{'peer_ids':block}))
    respond = await stor.execue(box.api, for_execue)

    while True:
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
            chat_id = chat['peer']['local_id']
            name = chat['chat_settings']['title']
            foreign = chat['peer']['id'] not in chats_in_vault
            result.append((foreign, chat_id,name))

    for_send = '\n'.join(map(lambda pair: f"{'! 'if pair[0] else ''}{pair[1]} : {pair[2]}", result))
    return (True, f"{len(result)} chats", for_send)
