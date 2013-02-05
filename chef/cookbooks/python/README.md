Description
===========

Installs and configures Python.  Also includes LWRPs for managing python packages with `pip` and `virtualenv` isolated Python environments.

Requirements
============

Platform
--------

* Debian, Ubuntu
* CentOS, Red Hat, Fedora

Cookbooks
---------

* build-essential

Attributes
==========

See `attributes/default.rb` for default values.

* `node["python"]["install_method"]` - method to install python with, default `package`.
* `node["python"]["distribute_install_py_version"]` - version of python to use when installing distribute. default '', specify version like '2.6' (uses python2.6 binary).

The file also contains the following attributes:

* platform specific locations and settings.
* source installation settings

Resource/Provider
=================

This cookbook includes LWRPs for managing:

* pip packages
* virtualenv isolated Python environments

`python_pip`
------------

Install packages using the new hotness in Python package management...[`pip`](http://pypi.python.org/pypi/pip).  Yo dawg...easy_install is so 2009, you better ask your local Pythonista if you don't know! The usage semantics are like that of any normal package provider.

# Actions

- :install: Install a pip package - if version is provided, install that specific version
- :upgrade: Upgrade a pip package - if version is provided, upgrade to that specific version
- :remove: Remove a pip package
- :purge: Purge a pip package (this usually entails removing configuration files as well as the package itself).  With pip packages this behaves the same as `:remove`

# Attribute Parameters

- package_name: name attribute. The name of the pip package to install
- version: the version of the package to install/upgrade.  If no version is given latest is assumed.
- virtualenv: virtualenv environment to install pip package into
- options: Add additional options to the underlying pip package command
- timeout: timeout in seconds for the command to execute. Useful for pip packages that may take a long time to install. Default 900 seconds.

# Example

    # install latest gunicorn into system path
    python_pip "gunicorn" do
      action :install
    end

    # target a virtualenv
    python_pip "gunicorn" do
      virtualenv "/home/ubunut/my_ve"
      action :install
    end

    # install Django 1.1.4
    python_pip "django" do
      version "1.1.4"
      action :install
    end

    # use this provider with the core package resource
    package "django" do
      provider Chef::Provider::PythonPip
      action :install
    end

`python_virtualenv`
-------------------

[`virtualenv`](http://pypi.python.org/pypi/virtualenv) is a great tool that creates isolated python environments.  Think of it as RVM without all those hipsters and tight jeans.

# Actions

- :create: creates a new virtualenv
- :delete: deletes an existing virtualenv

# Attribute Parameters

- path: name attribute. The path where the virtualenv will be created
- interpreter: The Python interpreter to use. default is `python2.6`
- owner: The owner for the virtualenv
- group: The group owner of the file (string or id)

# Example

    # create a 2.6 virtualenv owned by ubuntu user
    python_virtualenv "/home/ubuntu/my_cool_ve" do
      owner "ubuntu"
      group "ubuntu"
      action :create
    end

    # create a Python 2.4 virtualenv
    python_virtualenv "/home/ubuntu/my_old_ve" do
      interpreter "python2.4"
      owner "ubuntu"
      group "ubuntu"
      action :create
    end

Usage
=====

default
-------

Include default recipe in a run list, to get `python`, `pip` and `virtualenv`. Installs python by package or source depending on the platform.

package
-------

Installs Python from packages.

source
------

Installs Python from source.

pip
---

Installs `pip` from source.

virtualenv
----------

Installs virtualenv using the `python_pip` resource.

Changes
=======

## v1.0.4:

* [COOK-960] - add timeout to python_pip
* [COOK-651] - 'install_path' not correctly resolved when using python::source
* [COOK-650] - Add ability to specify version when installing distribute.
* [COOK-553] - FreeBSD support in the python cookbook

License and Author
==================

Author:: Seth Chisamore (<schisamo@opscode.com>)

Copyright:: 2011, Opscode, Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
