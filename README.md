
Cherry Servers ansible module 


Introductionv
------------

Cherry Servers is a bare-metal hosting company aimed at enterprise-level clients supports these Ansible modules:

* cherryservers_sshkey: manages public keys on Client Portal. Later on you may add those keys to deploying servers.
* cherryservers_ips: manages floating IPs at Client Portal. You may order additional IPs, route them to existing servers etc.
* cherryservers_server: manages servers at Cherry Servers. You can Deploy, Terminate server, manage its power etc.

Installation
------------

In order to use those modules you need to download module files from https://bitbucket.org/cherryservers/cherry_ansible_module and put them to folder named **library** and move it to folder with your ansible playbooks, i.e.:

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

The Cherry Servers module connects to Cherry Servers Public API via cherry-python package. You need to install it with pip:

```
$ pip install cherry-python
```

In order to use Ansible module you will need to export Cherry Servers API token. You can generate ant get token from Client Portal. The easiest way is to export variable like this:

```
$ export CHERRY_API_TOKEN="2b00042f7481c7b056c4b410d28f33cf"
```

Most of the time you will need several UUIDs or specific names to work with those modules:

* project_id - you will need to specify it to work with all modules. You can find that ID by looging to Cherry Servers Client Portal.
* plan_id - you will need to specify it to work with cherryservers_server module.
* image - you will need to specify it to work with cherryservers_server module.
* region - you will need to specify it to work with cherryservers_server and cherryservers_ips module.

Manage SSH keys
---------------

Adds raw ssh key to Client Portal:

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
Adds ssh key from file to Client Portal:

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

Manage Servers
--------------

Manage Floating IPs
-------------------
