import modules.basemaster as base
import modules.storage as stor


def get_id_from_word(word:str):
    partWithId = word.split('|')[0]
    supposedId = partWithId.replace('[id','').replace('[club','-')
    try:
        return int(supposedId)
    except:
        return False

class DataBox:

    handled_targets = None
    handled_chats = None


    def __init__(self,event):
        self.event = event

    @property
    def msg(self):
        return self.event.object.object.message

    @property
    def api(self):
        return self.event.api_ctx
    
    @property
    def command(self):
        try:
            return self.msg.text.split(' ')[1]
        except:
            return False

    @property
    def param(self):
        text_list = self.msg.text.split(' ')
        if len(text_list)>=4:
            return text_list[3]
        if len(text_list)==3:
            return text_list[2]
        
        return ""

    @property
    def admin_level(self):
        return base.get_admin_level(self.msg.from_id)

    def _get_targets(self):
        if self.handled_targets is not None:
            return self.handled_targets
        targets = []
        for word in self.msg.text.split(' '):
            targ = get_id_from_word(word)
            if targ:
                targets.append(targ)
        for fwd in self.msg.fwd_messages:
            targets.append(fwd.from_id)
        self.handled_targets = list(set(targets)-set([self.event.object.group_id*-1]))
        return self.handled_targets

    def _set_targets(self, targets:list):
        self.handled_targets = targets

    targets = property(_get_targets, _set_targets)
        
    def _get_chats(self):
        if self.handled_chats is not None:
            return self.handled_chats
        try:
            supposedGroup = self.msg.text.split(' ')[2]
        except:
            self.handled_chats = []
            return self.handled_chats

        chatList = []
        if supposedGroup == 'here':
            chatList =  [self.msg.peer_id]
        elif supposedGroup == 'all':
            chatList = list(stor.vault['chats'].keys())
        else:
            chatList = stor.vault['groups'].get(supposedGroup, False)
        if not chatList:
            try:
                chatList = list(map(int,supposedGroup.split(',')))
                chatList = [chat if chat>10000 else chat+2000000000 for chat in chatList]
            except:
                self.handled_chats = []
                return self.handled_chats

        admins_chats = base.get_chats_by_admin(self.msg.from_id)
        if 0 in admins_chats:
            self.handled_chats = chatList
        else:
            self.handled_chats = list(set(chatList).intersection(set(admins_chats)))
        return self.handled_chats

    def _set_chats(self, chats:list):
        self.handled_chats = chats

    chats = property(_get_chats, _set_chats)

    def remove_target(self, target):
        if self.handled_targets is None:
            return
        if target in self.handled_targets:
            self.handled_targets.remove(target)