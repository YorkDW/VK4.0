from modules.commands.utils import *

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
