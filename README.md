Cherry Servers ansible module 
=============================

Introduction
------------

Cherry Servers is a bare-metal hosting company aimed at enterprise-level clients supports these Ansible modules:

* __cherryservers_sshkey__: manages public keys on Client Portal. Later on you may add those keys to deploying servers.
* __cherryservers_ips__: manages floating IPs at Client Portal. You may order additional IPs, route them to existing servers etc.
* __cherryservers_server__: manages servers at Cherry Servers. You can Deploy, Terminate server, manage its power etc.

Installation
------------

In order to use those modules you need to download module files from [bitbucket](https://bitbucket.org/cherryservers/cherry_ansible_module) and put them to folder named **library** and move it to folder with your ansible playbooks, i.e.:

```
└── cherry_servers_playbooks
    ├── library
    │   ├── cherryservers_ips.py
    │   ├── cherryservers_server.py
    │   └── cherryservers_sshkey.py
    ├── servers_deploy.yml
    └── servers_terminate.yml
```

Requirements
------------

The Cherry Servers module connects to Cherry Servers Public API via [cherry-python](https://pypi.org/project/cherry-python/) package. You need to install it with __pip__:

```
$ pip install cherry-python
```

In order to use Ansible module you will need to export Cherry Servers API token. You can generate ant get token from Client Portal. The easiest way is to export variable like this:

```
$ export CHERRY_API_TOKEN="2b00042f7481c7b056c4b410d28f33cf"
```

Most of the time you will need several UUIDs or specific names to work with those modules:

* __project_id__ - you will need to specify it to work with all modules. You can find that ID by looging to Cherry Servers Client Portal.
* __plan_id__ - you will need to specify it to work with cherryservers_server module.
* __image__ - you will need to specify it to work with cherryservers_server module.
* __region__ - you will need to specify it to work with cherryservers_server and cherryservers_ips module.

Parameters - cherryservers_sshkey module
----------

Parameter   | Choices/Defaults   | Comments 
:-----------| :----------------- |:-----
__auth_token__  |                    | Authenticating API token provided by Cherry Servers. You can supply it via `CHERRY_AUTH_TOKEN` environement variable.
__label__       |                    | Label of SSH key.
__id__          |                    | ID of SSH key.
__fingerprint__ |                    | Fingerprint of SSH key.
__key_file__    |                    | Path to SSH key file.
__key__         |                    | RAW key
__state__       | __Choices__: _present, absent_ | Define desired state of SSH key

Manage SSH keys
---------------

Adds raw SSH key to Client Portal:

```
- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Add SSH key
    cherryservers_sshkey:
      label: "trylika"
      key: "ssh-rsa key-data comment"
      state: present
```

Adds SSH key from file to Client Portal:

```
- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Manage SSH keys
    cherryservers_sshkey:
      label: "keturiolika"
      key_file: key_file.pub
      state: present
```

Remove existing SSH key by label:
```
- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Removes SSH keys
    cherryservers_sshkey:
      label:
        - 'testas'
        - 'trylika'
      state: absent
```

Remove existing SSH key by ID:
```
- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Removes SSH keys
    cherryservers_sshkey:
      key_id:
        - '127'
        - '125'
      state: absent
```

Remove existing SSH key by fingerprint: 
```
- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Removes SSH keys
    cherryservers_sshkey:
      fingerprint:
        - 'cf:dc:ee:96:00:cb:c6:e2:fd:49:5c:64:0a:85:e9:47'
        - '88:b9:88:43:b3:24:53:55:85:88:61:cc:a0:7d:cb:f0'
      state: absent
```

Remove existing SSH key by file: 
```
- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Removes SSH keys
    cherryservers_sshkey:
      key_file:
        - key_file_jonas.pub
        - key_file_kestas.pub
        - key_file_mantas.pub
        - key_file_marius.pub
      state: absent
```

After you create a playbook just run playbook like this:

```
ansible-playbook ssh_key_add.yml
```

Parameters - cherryservers_server module
----------

Parameter   | Choices/Defaults   | Comments 
:-----------| :----------------- |:-----
__auth_token__      |                    | Authenticating API token provided by Cherry Servers. You can supply it via `CHERRY_AUTH_TOKEN` environement variable.
__project_id__      |                    |  ID of project of the servers.
__hostname__        |                    | Define hostname of server.
__image__           |                    | Image to install on the server, e.g. `Ubuntu 16.04 64bit`.
__ip_address__      |                    | List of floating IP addresses to add to new server.
__ip_address_id__   |                    |  List of floating IP addresses UIDs to add to new server.
__plan_id__         |                    | Plan for server creation.
__ssh_key_id__      |                    | SSH key`s ID to add SSH key to server.
__ssh_label__       |                    | SSH key`s label to add SSH key to server.
__server_ids__      |                    |  List of server`s IDs on which to operate.
__region__          |                    | Region of the server.
__cout__            | __default__: 1     | Amount of servers to create.
__count_offset__    | __default__: 1     | From which number to start the count.
__wait_timeout__    | __default__: 1800  | How long to wait for server to reach `active` state.
__state__            | __Choices__: _absent, active, rebooted, present, stopped, running_ | Define desired state of the server. If set to `present`, the module will return back immediately after API call returns. If set to `active`, the module will wait for `wait_timeout` for server to be in `active` state.

Manage Servers
--------------



Manage Floating IPs
-------------------
