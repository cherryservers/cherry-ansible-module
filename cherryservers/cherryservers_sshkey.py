#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: my_sample_module

short_description: This is my sample module

version_added: "2.4"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generatess
'''

import os
import time

from ansible.module_utils.basic import AnsibleModule

HAS_CHERRYSERVERS_SDK = True

try:
    import cherry
except ImportError:
    HAS_CHERRYSERVERS_SDK = False

MODULE_STATES = ['absent', 'present']


def run_module():

    module_args = dict(
        auth_token = dict(default=os.environ.get('CHERRY_AUTH_TOKEN'),
                          type = 'str',
                          no_log = True),
        state = dict(choices = MODULE_STATES, default = 'present'),
        key_id=dict(type='list', default=None),
        label=dict(type='list', default=None),
        fingerprint=dict(type='list', default=None),
        key=dict(type='list', default=None),
        key_file=dict(type='list', default=None)
    )

    mutually_exclusive=[
        ('key_id', 'label'),
        ('key_id', 'fingerprint'),
        ('label', 'fingerprint'),
        ('key', 'fingerprint'),
        ('key', 'key_id'),
        ('key', 'key_file')
    ]

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive = mutually_exclusive,
        supports_check_mode=True
    )

    if not HAS_CHERRYSERVERS_SDK:
        module.fail_json(msg='cherry required for this module')

    if not module.params.get('auth_token'):
        module.fail_json(msg='The "auth_token" parameter or ' +
            'CHERRY_AUTH_TOKEN environment variable is required')

    cherryservers_conn = cherry.Master(auth_token=module.params['auth_token'])

    state = module.params['state']

    if state in 'present':
        (changed, sshkey) = add_ssh_keys(module, cherryservers_conn)
    elif state == 'absent':
        (changed, sshkey) = remove_ssh_keys(module, cherryservers_conn)
    else:
        raise Exception("Unknown state: %s" % state)

    if module.check_mode:
        return result

    result['sshkey'] = sshkey
    result['changed'] = changed

    module.exit_json(**result)

def get_ids_for_keys(module, cherryservers_conn):

    """
    Function that returns ssh key ids on exit with
    input as label, ssh_key, fingerprint, key_id or
    path to file with key.
    """

    labels = module.params['label']
    key_file = module.params['key_file']
    ssh_key = module.params['key']
    key_id = module.params['key_id']
    fingerprint = module.params['fingerprint']

    ssh_keys = cherryservers_conn.get_ssh_keys()

    if labels:
        items = labels
        ssh_keys_dict = {"%s" % ssh_key['id'] : "%s" 
            % ssh_key['label'] for ssh_key in ssh_keys}

    elif ssh_key:
        items = ssh_key
        ssh_keys_dict = {"%s" % ssh_key['id'] : "%s" 
            % ssh_key['key'] for ssh_key in ssh_keys}

    elif fingerprint:
        items = fingerprint
        ssh_keys_dict = {"%s" % ssh_key['id'] : "%s" 
            % ssh_key['fingerprint'] for ssh_key in ssh_keys}

    elif key_id:
        items = key_id
        ssh_keys_dict = {"%s" % ssh_key['id'] : "%s" 
            % ssh_key['id'] for ssh_key in ssh_keys}

    elif key_file:
        items = []
        for key in key_file:
            with open(key) as key_file:
                ssh_key = key_file.read().rstrip()
            items.append(ssh_key)

        ssh_keys_dict = {"%s" % ssh_key['id'] : "%s" 
            % ssh_key['key'] for ssh_key in ssh_keys}

    else:
        msg = ("Unknown ssh key identifier, use one of: "
        "label, key_file, key, key_id, fingerprint")
        module.fail_json(msg=msg)

    uniq_dict = {}
    non_uniq_dict = {}

    for item in items:
        list_of_keys = []
        for key,value in ssh_keys_dict.items():
            if value == item:
                list_of_keys.append(key)
                uniq_dict[key] = value

        if len(list_of_keys) > 1:
            for key in list_of_keys:
                non_uniq_dict[key] = item

            msg = ("There are several keys with same value: %s. Please "
            "use \"ids\" in that case." % non_uniq_dict)
            module.fail_json(msg=msg)

    return list(uniq_dict.keys())

def add_ssh_keys(module, cherryservers_conn):

    """ 
    Function for adding SSH key to client portal. 
    """

    label = module.params['label']
    key_file = module.params['key_file']
    ssh_key = module.params['key']

    if len(label) == 1:
        label = label[0]

    if len(ssh_key) == 1:
        ssh_key = ssh_key[0]
    
    if len(key_file) == 1:
        key_file = key_file[0]

    changed = False

    if not label or ( not key_file and not ssh_key):
        msg = ("In order to add new key, you should "
        "provide both \"label\" and \"key\" or \"key_file\"")
        module.fail_json(msg=msg)

    if key_file:
        with open(key_file) as file:
            ssh_key = file.read()

    sshkey = cherryservers_conn.create_ssh_key(label, ssh_key)

    changed = True

    return (changed, sshkey)

def remove_ssh_keys(module, cherryservers_conn):

    """
    Function removes specified ssh keys. Returns changed
    in case of deletion of one of the keys.
    """

    changed = False

    ssh_keys = []
    changes = []

    key_ids = get_ids_for_keys(module, cherryservers_conn)

    for key_id in key_ids:
        (changed, sshkey) = remove_single_ssh_key(module, cherryservers_conn, key_id)
        ssh_keys.append(sshkey)
        changes.append(changed)

    if True in changes:
        changed = True

    return (changed, ssh_keys)

def remove_single_ssh_key(module, cherryservers_conn, key_id):

    """
    Function removes single ssh key. Returns object of ssh
    key and changed in case of deletion.
    """

    label = module.params['label']
    key_file = module.params['key_file']
    ssh_key = module.params['key']

    changed = False

    if label and (key_file or ssh_key):
        msg=("In order to remove key, you should "
        "provide only one argument of key")
        module.fail_json(msg=msg)

    sshkey = cherryservers_conn.delete_ssh_key(key_id)

    changed = True

    return (changed, sshkey)

def main():
    run_module()

if __name__ == '__main__':
    main()