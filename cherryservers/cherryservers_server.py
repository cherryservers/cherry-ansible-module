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

MODULE_STATES = ['absent', 'active', 'rebooted', 'present', 'stopped', 'running']

NAME_REGEX = r'({0}|{0}{1}*{0})'.format(r'[a-zA-Z0-9]', r'[a-zA-Z0-9\-]')
HOSTNAME_REGEX = r'({0}\.)*{0}$'.format(NAME_REGEX)

def run_module():

    module_args = dict(
        auth_token = dict(default=os.environ.get('CHERRY_AUTH_TOKEN'),
                          type = 'str',
                          no_log = True),
        hostname = dict(type = 'list'),
        new=dict(type='bool', required=False, default=False),
        count = dict(type = 'int', default = 1),
        count_offset = dict(type='int', default = 1),
        image = dict(),
        plan_id = dict(type = 'int'),
        project_id = dict(type = 'int', required = True),
        server_id = dict(type='int'),
        server_ids = dict(type='list'),
        region  = dict(),
        ssh_key_id = dict(type = 'list'),
        ssh_label = dict(type = 'list'),
        state = dict(choices = MODULE_STATES, default = 'present'),
        wait_timeout = dict(type = 'int', default = 1800)

    )

    mutually_exclusive = [
        ('hostname', 'server_ids'),
        ('ssh_key_id', 'ssh_label')
    ]

    required_one_of = [
        ('hostname', 'server_ids')
    ]

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_one_of = required_one_of,
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

    if state in ('present', 'active'):
        (changed, server) = create_multiple_servers(module, cherryservers_conn)

        if state == 'active':
            deploying_servers_ids = []

            if server:
                for srv in server:
                    srv_id = srv['id']
                    deploying_servers_ids.append(srv_id)

            wait_for_resource(module, cherryservers_conn, deploying_servers_ids)

    elif state == 'absent':

        (changed, server) = terminate_multiple_servers(module, cherryservers_conn)

    elif state in ('running', 'stopped', 'rebooted'):

        (changed, server) = servers_power(module, cherryservers_conn)
   
    else:
        raise Exception("Unknown state: %s" % state)

    if module.check_mode:
        return result

    result['server'] = server
    result['changed'] = changed

    module.exit_json(**result)


def provide_hostnames(module, cherryservers_conn):

    """ 
    Function for provide formatted list of hostnames

    Returns list of hostnames
    """

    count =  module.params['count']
    count_offset = module.params['count_offset']
    hostname = module.params['hostname']

    if len(hostname) == 1:
        hostname = hostname[0]

        if '%' in hostname:
            count_range = range(count_offset, count_offset + count)
            hostnames = [hostname % i for i in count_range]
        else:
            hostnames = [hostname] * count
    else:
        if count > 1:
            raise Exception("If you set several hostnames "
                "don't use \"count\" larger than 1.")
        hostnames = hostname

    # msg = "Type: %s Lenght: %s Hostnames: %s" % (type(hostname), len(hostname), hostnames)
    # raise Exception(msg)

    return hostnames

def get_ids_for_keys(module, cherryservers_conn):

    """
    Function that returns ssh key ids on exit with
    input as label, key_id.
    """

    labels = module.params['ssh_label']
    key_id = module.params['ssh_key_id']

    ssh_keys = cherryservers_conn.get_ssh_keys()

    if labels:
        items = labels
        ssh_keys_dict = {"%s" % ssh_key['id'] : "%s" 
            % ssh_key['label'] for ssh_key in ssh_keys}

    elif key_id:
        items = key_id
        ssh_keys_dict = {"%s" % ssh_key['id'] : "%s" 
            % ssh_key['id'] for ssh_key in ssh_keys}

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

def servers_power(module, cherryservers_conn):

    """
    Function to control power of several servers
    """

    state = module.params['state']

    changed = False

    servers = []
    changes = []

    server_ids = module.params['server_ids']

    if module.params['hostname']:

        hostnames = provide_hostnames(module, cherryservers_conn)
        server_ids = get_ids_from_hostnames(module, cherryservers_conn, hostnames)

    for server_id in server_ids:
        (changed, server) = server_power(module, cherryservers_conn, server_id, state)

        servers.append(server)
        changes.append(changed)

    if True in changes:
        changed = True

    return (changed, servers)

def server_power(module, cherryservers_conn, server_id, state):

    """
    Function to control server`s power
    """

    if state == 'stopped':
        server = cherryservers_conn.poweroff_server(server_id)
    elif state == 'running':
        server = cherryservers_conn.poweron_server(server_id)
    elif state == 'rebooted':
        server = cherryservers_conn.reboot_server(server_id)
    else:
        raise Exception("Unknown power state: %s" % state)

    changed = True
    
    return (changed, server)

def create_multiple_servers(module, cherryservers_conn):

    """
    Function for deploying multiple servers.
    """

    changed = False

    servers = []
    changes = []
    key_ids = []

    if module.params['ssh_label'] or module.params['ssh_key_id']:
        key_ids = get_ids_for_keys(module, cherryservers_conn)

    hostnames = provide_hostnames(module, cherryservers_conn)

    for hostname in hostnames:
        (changed, server) = create_server(module, cherryservers_conn, hostname, key_ids)

        # hostname = "%s.%s" % (index, hostname)
        # (changed, server) = test(hostname)

        servers.append(server)
        changes.append(changed)

    if True in changes:
        changed = True

    return (changed, servers)

def create_server(module, cherryservers_conn, hostname, ssh_keys):

    """
    Function for deploy of single server.
    """

    required_params = ('project_id', 'image', 'plan_id')

    for param in required_params:
        if not module.params.get(param):
            module.fail_json(
                msg="%s parameter is required for new server." % param)

    project_id = module.params['project_id']
    image = module.params['image']
    region = module.params['region']
    plan_id = module.params['plan_id']

    ips = []

    server = cherryservers_conn.create_server(
        project_id=project_id,
        hostname=hostname,
        image=image,
        region=region,
        ip_addresses=ips,
        ssh_keys=ssh_keys,
        plan_id=plan_id)

    changed = True

    return (changed, server)

def wait_for_resource(module, cherryservers_conn, deploying_servers_ids):

    """
    Function waits for servers to be active ant
    reachable.
    """

    wait_timeout = module.params['wait_timeout']

    wait_step = 10

    wait_timeout = time.time() + wait_timeout

    while wait_timeout > time.time():
        time.sleep(wait_step)

        current_states = []
        for server_id in deploying_servers_ids:
            current_server = cherryservers_conn.get_server(server_id)
            if 'id' in current_server:
                current_states.append(current_server['state'])

        if all(state == 'active' for state in current_states):
            return 

    raise Exception("Timed out waiting for active device: %s" % server_id)

def get_ids_from_hostnames(module, cherryservers_conn, hostnames):

    """
    Functions returns list of server_ids getted from hostnames
    in case if hostname is uniq for specified project.
    """

    #hostnames = module.params['hostname']
    project_id = module.params['project_id']

    current_servers = cherryservers_conn.get_servers(project_id)

    sid_host_dict = {"%s" % server['id'] : "%s" % server['hostname'] for server in current_servers}

    # Ensure to return only ids for servers with uniq hostname,
    # if there are servers with same hostname suggest to use
    # server_ids instead.
    uniq_sid_host_dic = {}
    non_uniq_sid_host_dic = {}

    for hostname in hostnames:
        list_of_keys = []
        for key,value in sid_host_dict.items():
            if value == hostname:
                list_of_keys.append(key)
                uniq_sid_host_dic[key] = value
        if len(list_of_keys) > 1:
            for key in list_of_keys:
                non_uniq_sid_host_dic[key] = hostname

            msg = ("There are several servers with same hostname: %s. Please "
            "use \"server_ids\" in that case." % non_uniq_sid_host_dic)
            module.fail_json(msg=msg)

    return list(uniq_sid_host_dic.keys())

def terminate_multiple_servers(module, cherryservers_conn):

    """ 
    Function for termination of several servers.
    Returns 'changed' in case of termination of 
    one of the servers.

    Function doesn't wait for complete termination.
    """

    changed = False

    servers = []
    changes = []

    server_ids = module.params['server_ids']

    if module.params['hostname']:

        hostnames = provide_hostnames(module, cherryservers_conn)
        server_ids = get_ids_from_hostnames(module, cherryservers_conn, hostnames)

    for server_id in server_ids:
        (changed, server) = terminate_server(module, cherryservers_conn, server_id)
        servers.append(server)
        changes.append(changed)

    if True in changes:
        changed = True

    return (changed, servers)

def terminate_server(module, cherryservers_conn, server_id):

    """ 
    Function for termination of single server.
    Returns server object if available and 'changed'
    if server was terminated.

    Function doesn't wait for complete termination.
    """

    changed = False

    current_server = cherryservers_conn.get_server(server_id)

    if 'id' in current_server:

        if current_server['state'] == 'terminating':
            server = current_server
            changed = False
        else:
            server = cherryservers_conn.terminate_server(
                server_id=server_id
            )
            changed = True

    elif 'code' in current_server and current_server['code'] == 404:

        server = None
        changed = False

    return (changed, server)

def main():
    run_module()

if __name__ == '__main__':
    main()