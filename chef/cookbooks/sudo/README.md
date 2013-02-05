DESCRIPTION
===========

This cookbook installs sudo and configures the /etc/sudoers file.

REQUIREMENTS
============

Requires that the platform has a package named sudo and the sudoers file is /etc/sudoers.

ATTRIBUTES
==========

The following attributes are set to blank arrays:

    node['authorization']['sudo']['groups']
    node['authorization']['sudo']['users']

They are passed into the sudoers template which iterates over the values to add sudo permission to the specified users and groups.

If you prefer to use passwordless sudo just set the following attribute to true:

    node['authorization']['sudo']['passwordless']

USAGE
=====

To use this cookbook, set the attributes above on the node via a role or the node object itself. In a role.rb:

    "authorization" => {
      "sudo" => {
        "groups" => ["admin", "wheel", "sysadmin"],
        "users" => ["jerry", "greg"],
        "passwordless" => true
      }
    }

In JSON (role.json or on the node object):

    "authorization": {
      "sudo": {
        "groups": [
          "admin",
          "wheel",
          "sysadmin"
        ],
        "users": [
          "jerry",
          "greg"
        ],
        "passwordless": true
      }
    }

Note that the template for the sudoers file has the group "sysadmin" with ALL:ALL permission, though the group by default does not exist.

LICENSE AND AUTHOR
==================

Author:: Adam Jacob <adam@opscode.com>
Author:: Seth Chisamore <schisamo@opscode.com>

Copyright 2009-2011, Opscode, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
