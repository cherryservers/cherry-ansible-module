#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: cherryservers_storage
short_description: Adds, modifies or removes storage volumes.
description:
     - Adds, modifies or removes storage volumes.
version_added: "0.2"

options:
  state:
    description:
     - Define desired state of storage volume
    default: present
    choices: ['present', 'absent', 'update']
  auth_token:
    description:
      - Authenticating API token provided by Cherry Servers. You can supply it via
        CHERRY_AUTH_TOKEN environement variable.
    required: true
  project_id:
    description:
      - ID of the project
  storage_volume_id:
    description:
      - ID of the storage volume
  attach_to_id:
    description:
      - ID of the server
  attach_to_hostname:
    description:
      - Hostname of the server
  region:
    description:
      - Region of the storage volume
  size:
    description:
      - Storage volume size
  description:
    description:
      - Storage volume description

requirements:
  - "cherry"
  - "python >= 2.6"

author:
  -  "Andrius Jucius <andrius.jucius@cherryservers.com>"
'''

EXAMPLES = '''

# Some examples on how to manage storage volumes

# Request new storage volume
- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Request new storage volume
    cherryservers_storage:
    project_id : '79813'
    region : 'EU-Nord-1'
    size: 256
    description: 'my-new-storage-volume'
    state: present

# Attach storage to server
- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Attach volume to server
    cherryservers_storage:
    project_id: '79813'
    storage_volume_id: 388268
    state: update

# Detach storage from a server
- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Detach volume from a server
    cherryservers_storage:
    project_id: '79813'
    state: update

# Upgrade storage volume size and/or description
- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Detach volume from server
    cherryservers_storage:
    project_id: '79813'
    storage_volume_id: 388268
    size:512
    description: 'my-upgraded-storage-volume'
    state: update

# Delete storage volume
- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Delete storage volume
    cherryservers_storage:
    project_id: '79813'
    storage_volume_id: 388268
    state: absent
'''

RETURN = '''
changed:
    description: True if volume was added, modified or removed.
    type: bool
    sample: True
    returned: always
volume:
    description: Info ofstorage volume that was added, modified or removed.
    type: list
    sample: [
        {
            "id": "str",
            "description": "str",
            "href": "str",
            "region": "object",
            "attached_to": "object"
        }
    ]
    returned: always
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
        project_id = dict(type = 'int', default = None),
        storage_volume_id = dict(type = 'int', default = None),
        size = dict(type = 'int', default = None),
        description = dict(type = 'str', default = '', required = False),
        attach_to_server_id = dict(type = 'int', default = None),
        attach_to_server_hostname = dict(type = 'str', default = None),
        region=dict(type='str', default=None),
    )

    mutually_exclusive=[
        ('size', 'attach_to_id'),
        ('size', 'attach_to_hostname'),
    ]

    result = dict(
        changed=False
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=mutually_exclusive,
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
        (changed, volume) = request_storage_volume(module, cherryservers_conn)
    elif state == 'absent':
        (changed, volume) = remove_storage_volume(module, cherryservers_conn)
    elif state == 'update':
        (changed, volume) = update_storage_volume(module, cherryservers_conn)
    else:
        raise Exception("Unknown state: %s" % state)

    if module.check_mode:
        return result

    result['volume'] = volume
    result['changed'] = changed

    module.exit_json(**result)


def request_storage_volume(module, cherryservers_conn):

    """
    Request elastic storage volume
    """

    check_required_params(module, ("project_id", "size"))

    project_id = module.params['project_id']
    size = module.params['size']
    description = module.params['description']
    region = module.params['region']
    attach_to = module.params['attach_to_server_id']
    hostname = module.params['attach_to_server_hostname']

    if hostname:
        attach_to = get_server_id_by_hostname(module, cherryservers_conn, hostname)

    volume = cherryservers_conn.create_storage_volume(
        project_id=project_id,
        size=size,
        description=description,
        region=region,
        attach_to=attach_to,
        fields="id")

    check_for_errors(module, volume)

    if attach_to:
        attachment = cherryservers_conn.attach_storage_volume(
            project_id=project_id,
            storage_id=volume['id'],
            server_id=attach_to,
            fields="id")

        check_for_errors(module, attachment)

    changed = True

    return (changed, volume)


def remove_storage_volume(module, cherryservers_conn):

    """
    Removes storage volume from the project
    """

    check_required_params(module, ('project_id', 'storage_volume_id'))

    project_id = module.params['project_id']
    storage_volume_id = module.params['storage_volume_id']

    remove_resp = cherryservers_conn.remove_storage_volume(
        project_id=project_id, storage_id=storage_volume_id)

    if remove_resp:
        check_for_errors(module, remove_resp)

    changed = True

    return (changed, remove_resp)


def update_storage_volume(module, cherryservers_conn):

    """
    Function updates storage volume.
    """

    check_required_params(module, ('project_id', 'storage_volume_id'))

    project_id = module.params['project_id']
    storage_volume_id = module.params['storage_volume_id']
    attach_to = module.params['attach_to_server_id']
    hostname = module.params['attach_to_server_hostname']
    size = module.params['size']

    if size:
        return upgrade_volume_size(module, cherryservers_conn)

    volume = cherryservers_conn.get_storage_volume(
        project_id=project_id,
        storage_id=storage_volume_id,
        fields="id,attached_to")

    check_for_errors(module, volume)

    if hostname:
        attach_to = get_server_id_by_hostname(module, cherryservers_conn, hostname)

    if 'attached_to' in volume and not attach_to:
        return detach_volume(module, cherryservers_conn)
    elif attach_to:
        return attach_volume(module, cherryservers_conn, attach_to)

    return (False, None)


def detach_volume(module, cherryservers_conn):

    """
    Function detach storage from server.
    """

    project_id = module.params['project_id']
    storage_volume_id = module.params['storage_volume_id']

    volume = cherryservers_conn.detach_storage_volume(
        project_id=project_id,
        storage_id=storage_volume_id,
        fields="id")

    if volume:
        check_for_errors(module, volume)

    changed = True

    return (changed, volume)


def attach_volume(module, cherryservers_conn, attach_to):

    """
    Function attach storage to server.
    """

    project_id = module.params['project_id']
    storage_volume_id = module.params['storage_volume_id']

    volume = cherryservers_conn.attach_storage_volume(
        project_id=project_id,
        storage_id=storage_volume_id,
        server_id=attach_to,
        fields="id")

    check_for_errors(module, volume)

    changed = True

    return (changed, volume)


def upgrade_volume_size(module, cherryservers_conn):
    """
    Function upgrades storage volume size.
    """

    project_id = module.params['project_id']
    storage_volume_id = module.params['storage_volume_id']
    size = module.params['size']
    description = module.params['description']

    volume = cherryservers_conn.update_storage_volume(
        project_id=project_id,
        storage_id=storage_volume_id,
        size=size,
        description=description,
        fields="id")

    check_for_errors(module, volume)

    changed = True

    return (changed, volume)


def get_server_id_by_hostname(module, cherryservers_conn, hostname):

    """
    Function returns server ID by it's hostname
    in case if hostname is uniq for specified project.
    """

    project_id = module.params['project_id']

    current_servers = cherryservers_conn.get_servers(project_id)

    check_for_errors(module, current_servers)

    sid_host_dict = {"%s" % server['id'] : "%s" % server['hostname'] for server in current_servers}

    # Ensure to return only ids for servers with uniq hostname,
    # if there are servers with same hostname suggest to use
    # server_ids instead.
    uniq_sid_host_dic = {}

    list_of_keys = []
    for key,value in sid_host_dict.items():
        if value == hostname:
            list_of_keys.append(key)
            uniq_sid_host_dic[key] = value
    if len(list_of_keys) > 1:
        msg = ("There are several servers with same hostname: %s. Please "
        "use \"attach_to_server_id\" in that case." % hostname)
        module.fail_json(msg=msg)
    elif not list_of_keys:
        msg = ("There are no server with hostname: %s. Please double check hoostname or "
        "use \"attach_to_server_id\" in that case." % hostname)
        module.fail_json(msg=msg)

    return list_of_keys[0]


def check_for_errors(module, server):

    if 'code' in server and (server['code'] == 404 or server['code'] == 400):
        return module.fail_json(msg=server['message'])
    else:
        return

def check_required_params(module, req_params):
    for param in req_params:
        if not module.params.get(param):
            module.fail_json(
                msg="%s parameter is required." % param)


def main():
    run_module()

if __name__ == '__main__':
    main()
