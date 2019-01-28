Cherry Servers ansible module 
=============================

Introduction
------------

Cherry Servers is an international Bare Metal Cloud provider and supports the following Ansible modules:

* __cherryservers_sshkey__: manages public SSH keys on Client Portal. You may assign these keys to your chosen servers upon deployment.
* __cherryservers_ips__: manages floating IPs at Client Portal. You may order additional IPs, route them to existing servers, etc.
* __cherryservers_server__: manages servers at Cherry Servers. You may Deploy and Terminate servers, manage theyr power, etc.

Installation
------------

In order to use above mentioned modules you need to download files from [bitbucket](https://bitbucket.org/cherryservers/cherry_ansible_module) , put them into folder named **library** and move it to your ansible playbooks directory, for instance:

```
└── cherry_servers_playbooks
    ├── library
    │   ├── cherryservers_ips.py
    │   ├── cherryservers_server.py
    │   └── cherryservers_sshkey.py
    ├── servers_deploy.yml
    └── servers_terminate.yml
```

Requirements
------------

The Cherry Servers module connects to Cherry Servers Public API via [cherry-python](https://pypi.org/project/cherry-python/) package. You need to install it with __pip__:

```
$ pip install cherry-python
```

In order to use Ansible module you will need to export Cherry Servers API token. You can generate and get it from your Client Portal. The easiest way is to export variable like this:

```
$ export CHERRY_AUTH_TOKEN="2b00042f7481c7b056c4b410d28f33cf"
```

Most of the time you will need several UUIDs or specific names to work with those modules:

* __project_id__ - you will need to specify it to work with all modules. You can find that ID by looging to Cherry Servers Client Portal.
* __plan_id__ - you will need to specify it to work with cherryservers_server module.
* __image__ - you will need to specify it to work with cherryservers_server module.
* __region__ - you will need to specify it to work with cherryservers_server and cherryservers_ips module.


Manage SSH keys
---------------

* cherryservers_sshkey module

Parameter   | Choices/Defaults   | Comments 
:-----------| :----------------- |:-----
__auth_token__  | __Required__: true                   | Authenticating API token provided by Cherry Servers. You can supply it via `CHERRY_AUTH_TOKEN` environement variable.
__label__       |                    | Label of SSH key.
__id__          |                    | ID of SSH key.
__fingerprint__ |                    | Fingerprint of SSH key.
__key_file__    |                    | Path to SSH key file.
__key__         |                    | RAW key
__state__       | __Choices__: _present, absent_ | Define desired state of SSH key

Add new SSH key from raw input to Client Portal:

```
# ssh_add_keys.yml

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

Add new SSH key from selected file to Client Portal:

```
# ssh_add_keys.yml

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
# ssh_remove_keys.yml

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
# ssh_remove_keys.yml

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
# ssh_remove_keys.yml

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
# ssh_remove_keys.yml

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

After you have created a playbook, you can run it like this:

```
ansible-playbook ssh_add_keys.yml
```

Manage Servers
--------------

* cherryservers_server module

Parameter   | Choices/Defaults   | Comments 
:-----------| :----------------- |:-----
__auth_token__      | __Required__: true | Authenticating API token provided by Cherry Servers. You can supply it via `CHERRY_AUTH_TOKEN` environement variable.
__project_id__      | __Required__: true |  ID of project of the servers.
__hostname__        |                    | Define hostname of server. You may specify `%02d` or `%03d` depending how many servers you need - dozens or hundreds. By specifying `%02d` with count `3`, you will get hostnames numerated from `01` to `03`, in case of `%03d` it will generate range from `001` to `003`.
__image__           |                    | Image to be installed on the server, e.g. `Ubuntu 16.04 64bit`.
__ip_address__      |                    | List of floating IP addresses to be added to new server.
__ip_address_id__   |                    |  List of floating IP addresses UIDs to be added to a new server.
__plan_id__         |                    | Plan for server creation.
__ssh_key_id__      |                    | SSH key`s ID for adding SSH key to server.
__ssh_label__       |                    | SSH key`s label for adding SSH key to server.
__server_ids__      |                    |  List of servers' IDs on which to operate.
__region__          |                    | Region of the server.
__cout__            | __default__: 1     | Amount of servers to be created.
__count_offset__    | __default__: 1     | From which number to start the count.
__wait_timeout__    | __default__: 1800  | How long to wait for server to reach `active` state.
__state__            | __Choices__: _absent, active, rebooted, present, stopped, running_ | Define desired state of the server. If set to `present`, the module will return back immediately after API call returns. If set to `active`, the module will wait for `wait_timeout` for server to be in `active` state.

Deploy server with selected SSH keys on it

```
# server_deploy.yml

- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Deploy CherryServers Server
    cherryservers_server:
      hostname:
        - server%02d.example.com
      plan_id: '161'
      project_id: '79813'
      image: 'Ubuntu 16.04 64bit'
      region: 'EU-East-1'
      state: present
      count: 1
      count_offset: 4
      ssh_label:
        - john
        - marius
```

Terminate servers

```
# server_terminate.yml

- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Remove CherryServers server
    cherryservers_server:
      project_id: '79813'
      hostname:
        - 'server03.example.com'
        - 'server04.example.com'
        - 'server06.example.com'
      state: absent
```

Deploy servers and wait for them to be active

```
# server_deploy.yml

- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Deploy CherryServers Server
    cherryservers_server:
      hostname:
        - server%02d.example.com
      plan_id: '161'
      project_id: '79813'
      image: 'Ubuntu 16.04 64bit'
      region: 'EU-East-1'
      state: active
      count: 2
      count_offset: 1
```

After you have created a playbook, just run it like this:

```
ansible-playbook server_deploy.yml
```

Manage Floating IPs
-------------------

* cherryservers_ips module

Parameter   | Choices/Defaults   | Comments 
:-----------| :----------------- |:-----
__auth_token__          | __Required__: true | Authenticating API token provided by Cherry Servers. You can supply it via `CHERRY_AUTH_TOKEN` environement variable.
__project_id__          | __Required__: true | ID of project of the servers.
__ptr_record__          |                    | Your preferable reverse
__ia_record__           |                    | Easy memorizable hostname
__routed_to_ip__        |                    | IP address of the server to route Floating IP to.
__routed_to_hostname__  |                    |  Hostname of the server to route Floating IP to.
__routed_to_server_id__ |                    | Server ID of the server to route Floating IP to.
__ip_address_id__       |                    | Floating IP address ID to update or remove.
__ip_address__          |                    | Floating IP address to be updated or removed.
__region__              |                    | Region of the Floating IP address.
__cout__                | __default__: 1     | Count of Floating IP addresses to be added.
__state__               | __Choices__: _present, absent, update_ | Define desired state of the IPs.

Add one Floating IP routed to server`s IP address

```
# ip_add.yml

- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Manage IP addresses
    cherryservers_ips:
    project_id : '79813'
    region : 'EU-East-1'
    ptr_record : 'your-preferable-reverse.example.com'
    a_record : 'easy-memorizable-hostname.cloud.cherryservers.com'
    routed_to_ip: 'xxx.xxx.xxx.xxx'
    state: present
```

Add several Floating IPs routed to server`s hostname

```
# ip_add.yml

- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Manage IP addresses
    cherryservers_ips:
    project_id : '79813'
    region : 'EU-East-1'
    ptr_record : 'your-preferable-reverse.example.com'
    a_record : 'easy-memorizable-hostname.cloud.cherryservers.com'
    routed_to_hostname: 'server04.example.com'
    state: present
```

Modify Floating IP route to different server`s hostname

```
# ip_update.yml

- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Manage IP addresses
    cherryservers_ips:
    project_id: '79813'
    ip_address_id: '2593fd9b-a0a1-10ce-13ce-2f7d7ad99eca'
    ptr_record: 'your-preferable-reverse.example.com'
    routed_to_hostname: easy-memorizable-hostname
    a_record: 'arturas1'
    state: update
```

Remove specific Floating IP address

```
# ip_terminate.yml

- name: Cherry Servers API module
  connection: local
  hosts: localhost
  tasks:
  - name: Manage IP addresses
    cherryservers_ips:
    project_id: '79813'
    ip_address: 
      - 'xxx.xxx.xxx.xxx'
    state: absent
```

After you have created a playbook, just run it like this:

```
ansible-playbook ip_add.yml
```