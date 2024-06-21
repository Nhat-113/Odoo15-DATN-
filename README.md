[![Build Status](https://runbot.odoo.com/runbot/badge/flat/1/master.svg)](https://runbot.odoo.com/runbot)
[![Tech Doc](https://img.shields.io/badge/master-docs-875A7B.svg?style=flat&colorA=8F8F8F)](https://www.odoo.com/documentation/15.0)
[![Help](https://img.shields.io/badge/master-help-875A7B.svg?style=flat&colorA=8F8F8F)](https://www.odoo.com/forum/help-1)
[![Nightly Builds](https://img.shields.io/badge/master-nightly-875A7B.svg?style=flat&colorA=8F8F8F)](https://nightly.odoo.com/)

Odoo
----

Odoo is a suite of web based open source business apps.

The main Odoo Apps include an <a href="https://www.odoo.com/page/crm">Open Source CRM</a>,
<a href="https://www.odoo.com/app/website">Website Builder</a>,
<a href="https://www.odoo.com/app/ecommerce">eCommerce</a>,
<a href="https://www.odoo.com/app/inventory">Warehouse Management</a>,
<a href="https://www.odoo.com/app/project">Project Management</a>,
<a href="https://www.odoo.com/app/accounting">Billing &amp; Accounting</a>,
<a href="https://www.odoo.com/app/point-of-sale-shop">Point of Sale</a>,
<a href="https://www.odoo.com/app/employees">Human Resources</a>,
<a href="https://www.odoo.com/app/social-marketing">Marketing</a>,
<a href="https://www.odoo.com/app/manufacturing">Manufacturing</a>,
<a href="https://www.odoo.com/">...</a>

Odoo Apps can be used as stand-alone applications, but they also integrate seamlessly so you get
a full-featured <a href="https://www.odoo.com">Open Source ERP</a> when you install several Apps.

Getting started with Odoo
-------------------------

For a standard installation please follow the <a href="https://www.odoo.com/documentation/15.0/administration/install.html">Setup instructions</a>
from the documentation.

To learn the software, we recommend the <a href="https://www.odoo.com/slides">Odoo eLearning</a>, or <a href="https://www.odoo.com/page/scale-up-business-game">Scale-up</a>, the <a href="https://www.odoo.com/page/scale-up-business-game">business game</a>. Developers can start with <a href="https://www.odoo.com/documentation/15.0/developer/howtos.html">the developer tutorials</a>

### Branch Strategy

- `develop`
  - Default branch for development
  - Specification written in this branch's latest commit should work at development environment
  - Do not commit to `develop` directly
    - If you want to add/change documents, send pull request to this branch
- `master`
  - Specification written in this branch's latest commit should work at production environment
  - Do not commit to `master` directly
    - If you want to add/change documents in this branch, send pull request to this branch


## Installation

### Ubuntu

※ Require: Python3.8 installed

※ Install packages:

```
  sudo apt install python3.8-venv
  sudo apt update
  sudo apt install gcc
  sudo apt install build-essential
  sudo apt-get install python3.8-dev

  python3.8 -m venv .<your-venv>
  source ./<your-venv>/bin/activate

  pip3 install -r requirements.txt
```

※ Debugger: VSCode -> Run -> Add Configuration -> Python Debugger -> Python File

1. Create your odoo config file: `odoo.conf`

```
[options]
addons_path = ./addons, ./custom-addons, ./odoo/addons

# db_host = postgres
# db_password = odoo
db_port = 5432
admin_passwd = 1
# csv_internal_sep = ,
# proxy_mode = True
# db_name = odoo2
# db_maxconn = 64
# db_sslmode = prefer
# db_template = template0
dbfilter = odoo15
# socket_port = 5555z
# demo = {}
# email_from = False
# from_filter = False
# http_interface =
# http_port = 8069
# limit_memory_hard = 13690208256
# limit_memory_soft = 11408506880
# limit_request = 8192
# limit_time_cpu = 600
# limit_time_real = 1200
# longpolling_port = 8072
# http_enable = True
# max_cron_threads = 1
workers = 0
```

2. Edit launch.json

```markdown
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Odoo",
      "type": "python",
      "request": "launch",
      "stopOnEntry": false,
      "console": "integratedTerminal",
      "python": "${workspaceFolder}/<your-venv>/bin/python3", // link to your .venv folder
      "program": "${workspaceFolder}/odoo-bin",
      "args": [
        "--config=${workspaceFolder}/odoo.conf",
        // "--database=tutor1,tutor2",
        // "--update=nama_folder1,nama_folder2"
      ]
    }
  ]
}
```
