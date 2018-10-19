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
    description: The output message that the sample module generates
'''

import os
import time

from ansible.module_utils.basic import AnsibleModule

HAS_CHERRYSERVERS_SDK = True

try:
    import cherry
except ImportError:
    HAS_CHERRYSERVERS_SDK = False

MODULE_STATES = ['absent', 'present', 'update']


def run_module():

    module_args = dict(
        auth_token = dict(default=os.environ.get('CHERRY_AUTH_TOKEN'),
                          type = 'str',
                          no_log = True),
        state = dict(choices = MODULE_STATES, default = 'present'),
        project_id = dict(type = 'int', default=None),
        type = dict(type='str', default=None),
        ptr_record=dict(type='str', default=None),
        a_record=dict(type='str', default=None),
        assigned_to=dict(type='str', default=None),
        routed_to=dict(type='str', default=None),
        routed_to_ip=dict(type='str', default=None),
        routed_to_hostname=dict(type='str', default=None),
        routed_to_server_id=dict(type='str', default=None),
        region=dict(type='str', default=None),
        ip_address_id=dict(type='list', default=None),
        ip_address=dict(type='list', default=None),
        count = dict(type = 'int', default = 1)
    )

    mutually_exclusive=[
        ('routed_to_ip', 'routed_to_hostname'),
        ('routed_to_ip', 'routed_to_server_id'),
        ('routed_to_hostname', 'routed_to_server_id'),
        ('key', 'key_id'),
        ('key', 'key_file'),
        ('ip_address_id', 'ip_address')
    ]

    result = dict(
        changed=False
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
        #(changed, ip) = add_ip_address(module, cherryservers_conn)
        (changed, ip) = add_multiple_ip_addresses(module, cherryservers_conn)
    elif state == 'absent':

        ip_address_id = module.params['ip_address_id']
        #(changed, ip) = remove_ip_address(module, cherryservers_conn, ip_address_id)
        (changed, ip) = remove_multiple_ip_addresses(module, cherryservers_conn)
    elif state == 'update':

        ip_address_id = module.params['ip_address_id']
        (changed, ip) = update_ip_address(module, cherryservers_conn, ip_address_id)
    else:
        raise Exception("Unknown state: %s" % state)

    if module.check_mode:
        return result

    result['ip_address'] = ip
    result['changed'] = changed

    module.exit_json(**result)

def add_multiple_ip_addresses(module,cherryservers_conn):

    """
    Adds several ips 
    """

    changed = False
    
    i = 0
    ips = []
    changes = []

    count = module.params['count']

    while i < count:
        (changed, ip) = add_ip_address(module, cherryservers_conn)

        ips.append(ip)
        changes.append(changed)
        i += 1

    if True in changes:
        changed = True

    return (changed, ips)


def add_ip_address(module, cherryservers_conn):

    """
    Adds floating ip
    """

    required_params = ["project_id"]

    for param in required_params:
        if not module.params.get(param):
            module.fail_json(
                msg="%s parameter is required for new ip." % param)

    project_id = module.params['project_id']
    ip_type = module.params['type']
    ptr_record = module.params['ptr_record']
    a_record = module.params['a_record']
    assigned_to = module.params['assigned_to']
    routed_to = module.params['routed_to']
    region = module.params['region']

    ip_id = get_id_for_ip(module, cherryservers_conn)

    if ip_id:
        routed_to = ip_id

    ip = cherryservers_conn.create_ip_address(
        project_id=project_id,
        ip_type=ip_type,
        region=region,
        ptr_record=ptr_record,
        a_record=a_record,
        routed_to=routed_to,
        assigned_to=assigned_to)

    changed = True

    return (changed, ip)

def remove_multiple_ip_addresses(module, cherryservers_conn):

    changed = False

    ips = []
    changes = []

    floating_ip_uids = get_id_of_floating_ip(module, cherryservers_conn)

    for floating_ip_uid in floating_ip_uids:
        (changed, ip) = remove_ip_address(module, cherryservers_conn, floating_ip_uid)
        ips.append(ip)
        changes.append(changed)

    if True in changes:
        changed = True

    return (changed, ips)

def remove_ip_address(module, cherryservers_conn, ip_address_id):

    """
    Removes IP address from the project
    """

    required_params = ('project_id', 'state')

    for param in required_params:
        if not module.params.get(param):
            module.fail_json(
                msg="%s parameter is required for IP removal." % param)

    project_id = module.params['project_id']

    current_ip = cherryservers_conn.get_ip_address(project_id, ip_address_id)

    if 'id' in current_ip:
        ip = cherryservers_conn.remove_ip_address(project_id, ip_address_id)
        changed = True
    elif 'code' in current_ip and current_ip['code'] == 404:
        ip = None
        changed = False

    return (changed, ip)

def get_id_of_floating_ip(module, cherryservers_conn):

    """
    In order to remove floating IP by it's numeric IP
    address, we need to translate that IP to its UID

    Functions returns list or UIDs.
    """

    project_id = module.params['project_id']
    ip_address = module.params['ip_address']
    ip_address_id = module.params['ip_address_id']

    current_ips = cherryservers_conn.get_ip_addresses(project_id)

    if ip_address:
        items = ip_address
        keys_dict = {"%s" % ip['id'] : "%s" % ip['address'] 
            for ip in current_ips 
                if ip['type'] == 'floating-ip'}
    elif ip_address_id:
        items = ip_address_id
        keys_dict = {"%s" % ip['id'] : "%s" % ip['id'] 
            for ip in current_ips 
                if ip['type'] == 'floating-ip'}
    else:
        return

    uniq_dict = {}

    for item in items:
        for key,value in keys_dict.items():
            if value == item:
                uniq_dict[key] = value

    return list(uniq_dict.keys())
    

def get_id_for_ip(module, cherryservers_conn):

    """
    In order to route floating IP to servers IP we need
    to translate servers IP addresses to its UIDs.

    Function returns list or primary IP addresses where
    to route to.
    """

    project_id = module.params['project_id']
    routed_to_hostname = module.params['routed_to_hostname']
    routed_to_server_id = module.params['routed_to_server_id']
    routed_to_ip = module.params['routed_to_ip']

    current_servers = cherryservers_conn.get_servers(project_id)

    if routed_to_hostname:
        item = routed_to_hostname
        keys_dict = {"%s" % server['id'] : "%s" % server['hostname'] for server in current_servers}
    elif routed_to_server_id:
        item = routed_to_server_id
        keys_dict = {"%s" % server['id'] : "%s" % server['id'] for server in current_servers}
    elif routed_to_ip:
        item = routed_to_ip
        for server in current_servers:
            for ip_address in server['ip_addresses']:
                if ip_address['address'] == routed_to_ip:
                    keys_dict = {"%s" % server['id'] : "%s" % ip_address['address']}
    else:
        return
            
    uniq_dict = {}
    non_uniq_dict = {}

    list_of_keys = []
    for key,value in keys_dict.items():
        if value == item:
            list_of_keys.append(key)
            uniq_dict[key] = value

    if len(list_of_keys) > 1:
        for key in list_of_keys:
            non_uniq_dict[key] = item

        msg = ("There are several nodes with same hostname: %s. Please "
        "use \"routed_to_server_id\" instead." % non_uniq_dict)
        module.fail_json(msg=msg)

    for server in current_servers:
        if server['id'] == int(list(uniq_dict.keys())[0]):

            primary_ip_dict = {"%s" % ip_address['id'] : "%s" % ip_address['address'] 
                for ip_address in server['ip_addresses']
                    if ip_address['type'] == 'primary-ip'}

            if routed_to_ip:
                primary_ip_dict = {"%s" % ip_address['id'] : "%s" % ip_address['address'] 
                    for ip_address in server['ip_addresses']
                        if ip_address['address'] == routed_to_ip}

            if len(primary_ip_dict) > 1:
                msg = ("There are several primary IPs to route to: %s. Please "
                "use \"ip_address\" instead." % primary_ip_dict)
                module.fail_json(msg=msg)

    return list(primary_ip_dict.keys())[0]

def update_ip_address(module, cherryservers_conn, ip_address_id):

    """
    Function updates IP address with either
    A record, PRT record, assigned server etc.
    """

    required_params = ('project_id', 'ip_address_id')

    for param in required_params:
        if not module.params.get(param):
            module.fail_json(
                msg="%s parameter is required for ip update." % param)

    project_id = module.params['project_id']
    ptr_record = module.params['ptr_record']
    a_record = module.params['a_record']
    assigned_to = module.params['assigned_to']
    routed_to = module.params['routed_to']

    ip_id = get_id_for_ip(module, cherryservers_conn)

    routed_to = ip_id

    ip = cherryservers_conn.update_ip_address(
            project_id, 
            ip_address_id, 
            ptr_record, 
            a_record, 
            routed_to,
            assigned_to)

    changed = True

    return (changed, ip)

def main():
    run_module()

if __name__ == '__main__':
    main()
