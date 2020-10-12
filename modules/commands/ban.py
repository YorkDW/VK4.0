from modules.commands.utils import *
from modules.commands.kick import kick, remove_protected_targets
from modules.commands.delete import find_by, delete_msgs_by_ids, get_basic_params, transform_peer_ids

@log_and_respond_decorator
async def add_ban(box):
    kick_status, kick_answer, _ = await kick(box)
    if not kick_status:
        return (False, kick_answer, kick_answer)
    
    clear_msgs_flag = True if box.get_by_name('clear') else False

    completed = 0
    errors = []
    msg_ids = []
    for target in box.targets:
        for chat in box.chats:
            status, answer = await base.add_ban(target, chat)
            if status:
                completed += 1
            else:
                errors.append(answer)

        if clear_msgs_flag:
            params = get_basic_params()
            params['check_type'] = 'from_user'
            params['check_value'] = [target]
            params['peer_ids'] = transform_peer_ids(box.chats)
            msg_ids.extend(await find_by(params))

    if clear_msgs_flag:
        err_msgs = await delete_msgs_by_ids(msg_ids)


    await base.update_vault_banlist()
    answer = f"Banned {', '.join(map(str, box.targets))} {completed}/{len(box.targets)*len(box.chats)}"
    log = f"{answer} {', '.join(errors)[:100]}"

    if clear_msgs_flag:
        stat = f"{len(msg_ids)-len(err_msgs)}/{len(msg_ids)}"
        answer += f", messages deleted {stat}"
        log += stat

    return (True, log, answer)

@log_and_respond_decorator
async def del_ban(box):
    errors = check_zeros({"chats":box.chats, "targets":box.targets})
    if errors:
        return (False, errors, errors)

    completed = 0
    errors = []
    for target in box.targets:
        for chat in box.chats:
            status, answer = await base.del_ban(target, chat)
            if status:
                completed += 1
            else:
                errors.append(answer)
    
    await base.update_vault_banlist()
    answer = f"Forgiven {', '.join(map(str, box.targets))} {completed}/{len(box.targets)*len(box.chats)}"
    log = f"{answer} {', '.join(errors)[:100]}"
    return (True, log, answer)

@log_and_respond_decorator
async def add_perm_ban(box):
    box.chats = list(stor.vault["chats"].keys())
    kick_status, kick_answer, _ = await kick(box)
    if not kick_status:
        return (False, kick_answer, kick_answer)

    clear_msgs_flag = True if box.get_by_name('clear') else False

    banned_targets = []
    errors = []
    msg_ids = []
    for target in box.targets:
        status, answer = await base.add_perm_ban(target)
        if status:
            banned_targets.append(target)
        else:
            errors.append(answer)

        if clear_msgs_flag:
            params = get_basic_params()
            params['check_type'] = 'from_user'
            params['check_value'] = [target]
            params['peer_ids'] = transform_peer_ids(box.chats)
            msg_ids.extend(await find_by(params))
    
    if clear_msgs_flag:
        err_msgs = await delete_msgs_by_ids(msg_ids)
    
    await base.update_vault_banlist()
    answer = f"Fully banned: {', '.join(map(str, banned_targets))} {len(banned_targets)}/{len(box.targets)}"
    log = f"{answer} {', '.join(errors)}"

    if clear_msgs_flag:
        stat = f"{len(msg_ids)-len(err_msgs)}/{len(msg_ids)}"
        answer += f", messages deleted {stat}"
        log += stat

    return (True, log, answer)

@log_and_respond_decorator
async def del_perm_ban(box):
    errors = check_zeros({"targets":box.targets})
    if errors:
        return (False, errors, errors)
    
    unbanned_targets = []
    errors = []
    for target in box.targets:
        status, answer = await base.del_perm_ban(target)
        if status:
            unbanned_targets.append(target)
        else:
            errors.append(answer)

    await base.update_vault_banlist()
    answer = f"Not fully banned now: {', '.join(map(str, unbanned_targets))} {len(unbanned_targets)}/{len(box.targets)}"
    log = f"{answer} {', '.join(errors)}"
    return (True, log, answer)

     
    
    


