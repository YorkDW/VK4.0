from modules.commands.utils import *

@log_and_respond_decorator
async def add_chat(box):  # add a selection option for chat
    t_list = box.text_list()

    peer_id = box.get_by_name('target', int)
    if not peer_id:
        if box.msg.peer_id < 2*10**9:
            return (False, "pm was not added", "You can't add this dialog")
        if base.verify_chat(box.msg.peer_id):
            return (False, "Chat already added", "Chat already added")
        peer_id = box.msg.peer_id

    name = box.get_by_name('name') or str(peer_id-2*10**9)
 
    c_status, c_message = await base.add_chat(peer_id, name)
    if not c_status:
        return (False, message, message)
    else:
        c_message += f", with name {name}"

    group = box.get_by_name('group')
    if group in stor.vault['groups'].keys():
        g_status, g_message = await base.add_chat_to_group(peer_id, group)
        if not g_status:
            c_message += f" {g_message}"
        else:
            c_message += f", with group {group}"

    for user in box.targets:
        if user in stor.vault['admins'].keys():
            a_status, a_message = await base.add_admin_to_chat(peer_id, user)
            if not a_status:
                c_message += f" {user} {a_message}"
    await base.update_vault_all()
    return (True, c_message, c_message)

@log_and_respond_decorator
async def del_chat(box): # add a selection option for chat
    peer_id = box.get_by_name('target', int)
    if not peer_id:
        if box.msg.peer_id < 2*10**9:
            return (False, "pm was not deleted", "You can't del this dialog")
        if not base.verify_chat(box.msg.peer_id):
            return (False, "Chat was not added yet", "Chat was not added yet")
        peer_id = box.msg.peer_id
    status, message = await base.del_chat(peer_id)
    await base.update_vault_all()
    return (status, message, message)

@log_and_respond_decorator
async def add_admin(box):
    if not box.targets:
        return (False, "Wrong admin", "Choose admin")
    func = base.add_admin
    if box.targets[0] in stor.vault['admins'].keys():
        func = base.update_admin

    level = box.get_by_name('level', int)
    if not level:
        (False, "Wrong level", "Choose level")
    if level not in (1,2,3,4):
        return (False, "Wrong level", "Level must be from 1 to 4")

    name = box.get_by_name('name')
    if not name:
        if func == base.update_admin:
            name = stor.vault['admins'][box.targets[0]]['name']
        else:
            name = str(box.targets[0])

    status, message = await func(box.targets[0], level, name)
    await base.update_vault_admins()
    return (status, message, message)

@log_and_respond_decorator
async def del_admin(box):
    if len(box.targets) == 0:
        return (False, "Wrong admin", "Choose admin")
    if box.targets[0] not in stor.vault['admins'].keys():
        return (False, "No such admin", "Target is not an admin")
    status, message = await base.del_admin(box.targets[0])
    await base.update_vault_all()
    return (status, message, message)

@log_and_respond_decorator
async def add_group(box):
    name = box.get_by_name('name')
    if not name:
        return (False, "Wrong name", "Choose name")
    if name in stor.vault['groups'].keys():
        return (False, "Group already exists", "Group already exists")
    status, answer = await base.add_group(name)
    await base.update_vault_groups()
    return (status, answer, answer)

@log_and_respond_decorator
async def del_group(box):
    name = box.get_by_name('name')
    if not name:
        return (False, "Wrong name", "Choose name")
    if name in stor.vault['groups'].keys():
        return (False, "Group is not exists", "Group is not exists")

    status, answer = await base.del_group(name)
    await base.update_vault_groups()
    return (status, answer, answer)

async def admin_and_chat(box, add_or_delet):
    if add_or_delet not in ("add", "delet"):
        return (False, "WRONG ADD_OR_DELET NAME", "Internal error")
    func = base.add_admin_to_chat if add_or_delet=="add" else base.del_admin_from_chat
    
    errors = check_zeros({"Admin":box.targets, "Chats":box.chats})
    if errors:
        return (False, errors, errors)
    
    completed = 0
    add_errors = []
    for chat in box.chats:
        status, answer = await func(chat, box.targets[0])
        if status:
            completed += 1
        else:
            add_errors.append(answer)
    await base.update_vault_admins()
    log = ", ".join(add_errors) if add_errors else f"{add_or_delet}ed"
    return (completed != 0, log, f"{add_or_delet}ed {completed}/{len(box.chats)}")

@log_and_respond_decorator
async def add_admin_to_chat(box):
    return await admin_and_chat(box, "add")

@log_and_respond_decorator
async def del_admin_from_chat(box):
    return await admin_and_chat(box, "delet")

async def chat_and_group(box, add_or_delet):
    func = base.add_chat_to_group if add_or_delet=="add" else base.del_chat_from_group

    name = box.get_by_name('name')
    if not name:
        return (False, "Wrong name", "Choose name")
    if name not in stor.vault['groups'].keys():
        return (False, "Group is not exists", "Group is not exists")

    peer_id = box.get_by_name('target', int)
    if not peer_id:
        if box.msg.peer_id < 2*10**9:
            return (False, "pm was not added", "You can't add this dialog")
        if not base.verify_chat(box.msg.peer_id):
            return (False, "Chat does not exists", "Chat does not exists")
        peer_id = box.msg.peer_id
    

    status, answer = await func(peer_id, name)
    await base.update_vault_groups()
    return (status, answer, answer)

@log_and_respond_decorator
async def add_chat_to_group(box):
    return await chat_and_group(box, "add")

@log_and_respond_decorator
async def del_chat_from_group(box):
    return await chat_and_group(box, "delet")