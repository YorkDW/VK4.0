from modules.commands.utils import *
from modules.message import split_message_dict, get_message_resend_dict, send_new

# do as "broadcast + any func"

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

@log_and_respond_decorator
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
        return (False, "Nothing to broadcast", "Nothing to broadcast") 
    
    errors = check_zeros({"chat":box.chats})
    if errors:
        return (False, errors, errors)

    call_list = await get_call_list(box.api, box.chats) if box.param == "call" else {}

    for_execue = []
    for peer in box.chats:
        for_send_with_calls = for_send.copy()
        if peer in call_list.keys():
            for_send_with_calls["message"] += call_list[peer]
        msg_list = await split_message_dict(for_send_with_calls)
        for msg in msg_list:
            for_execue.append(("messages.send",msg.copy()))
            for_execue[-1][1].update({"peer_id":peer, "random_id":random.randint(50000,2000000000)})
    
    result = await stor.execue(box.api, for_execue)
    
    stat =  get_stat(result)
    return (True, f"Res {stat}", f"Broadcasted {stat}")