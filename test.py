import json

DLP_POLICY = json.load(open("pollicy.json","r"))

blacklist_sender, blacklist_receiver = DLP_POLICY['user']['blackList'].get('senderList', []), DLP_POLICY['user']['blackList'].get('receiverList', [])
whitelist_sender, whitelist_receiver = DLP_POLICY['user']['whiteList'].get('senderList', []), DLP_POLICY['user']['whiteList'].get('receiverList', [])
pii_not_present_default = DLP_POLICY['message']['messageType']['piiNotPresent'].get('default')
user_is_registered_default = DLP_POLICY['message']['userType']['userIsRegistered'].get('default')
user_not_registered_default = DLP_POLICY['message']['userType']['userNotRegistered'].get('default')
pii_list = DLP_POLICY.get('pii', [])


def isWhitelistUser(user):
    for email in whitelist_receiver + whitelist_sender:
        if user == email :
            return True
    return False
print(isWhitelistUser("husky@duck.com"))
