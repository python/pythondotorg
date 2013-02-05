Description
===========

Installs and configures MySQL client or server.

Requirements
============

Platform
--------

* Debian, Ubuntu
* CentOS, Red Hat, Fedora

Tested on:

* Debian 5.0
* Ubuntu 10.04
* CentOS 5.5

Cookbooks
---------

Requires Opscode's openssl cookbook for secure password generation.

Requires a C compiler and Ruby development package in order to build mysql gem with native extensions. On Debian and Ubuntu systems this is satisfied by installing the "build-essential" and "ruby-dev" packages before running Chef. See USAGE below for information on how to handle this during a Chef run.

Resources and Providers
=======================

The LWRP that used to ship as part of this cookbook has been refactored into the [database](https://github.com/opscode/cookbooks/tree/master/database) cookbook.  Please see the README for details on updated usage.

Attributes
==========

* `mysql['server_root_password']` - Set the server's root password with this, default is a randomly generated password with `OpenSSL::Random.random_bytes`.
* `mysql['server_repl_password']` - Set the replication user 'repl' password with this, default is a randomly generated password with `OpenSSL::Random.random_bytes`.
* `mysql['server_debian_password']` - Set the debian-sys-maint user password with this, default is a randomly generated password with `OpenSSL::Random.random_bytes`.
* `mysql['bind_address']` - Listen address for MySQLd, default is node's ipaddress.
* `mysql['data_dir']` - Location for mysql data directory, default is "/var/lib/mysql"
* `mysql['conf_dir']` - Location for mysql conf directory, default is "/etc/mysql"
* `mysql['ec2_path']` - location of mysql data_dir on EC2 nodes, default "/mnt/mysql"

Performance tuning attributes, each corresponds to the same-named parameter in my.cnf; default values listed

* `mysql['tunable']['key_buffer']`          = "250M"
* `mysql['tunable']['max_connections']`     = "800"
* `mysql['tunable']['wait_timeout']`        = "180"
* `mysql['tunable']['net_write_timeout']`   = "30"
* `mysql['tunable']['net_write_timeout']`   = "30"
* `mysql['tunable']['back_log']`            = "128"
* `mysql['tunable']['table_cache']`         = "128"
* `mysql['tunable']['max_heap_table_size']` = "32M"
* `mysql['tunable']['expire_logs_days']`    = "10"
* `mysql['tunable']['max_binlog_size']`     = "100M"

Usage
=====

On client nodes,

    include_recipe "mysql::client"

This will install the MySQL client libraries and development headers on the system. It will also install the Ruby Gem `mysql`, so that the cookbook's LWRP (above) can be used. This is done during the compile-phase of the Chef run. On platforms that are known to have a native package (currently Debian, Ubuntu, Red hat, Centos, Fedora and SUSE), the package will be installed. Other platforms will use the RubyGem.

This creates a resource object for the package and does the installation before other recipes are parsed. You'll need to have the C compiler and such (ie, build-essential on Ubuntu) before running the recipes, but we already do that when installing Chef :-). 

On server nodes,

    include_recipe "mysql::server"

On Debian and Ubuntu, this will preseed the mysql-server package with the randomly generated root password from the attributes file. On other platforms, it simply installs the required packages. It will also create an SQL file, /etc/mysql/grants.sql, that will be used to set up grants for the root, repl and debian-sys-maint users.

On EC2 nodes,

    include_recipe "mysql::server_ec2"

When the `ec2_path` doesn't exist we look for a mounted filesystem (eg, EBS) and move the data_dir there.

The client recipe is already included by server and 'default' recipes.

For more infromation on the compile vs execution phase of a Chef run:

* http://wiki.opscode.com/display/chef/Anatomy+of+a+Chef+Run

Changes/Roadmap
===============

### v1.2.2

* [COOK-826] mysql::server recipe doesn't quote password string
* [COOK-834] Add 'scientific' and 'amazon' platforms to mysql cookbook

### v1.2.1

* [COOK-644] Mysql client cookbook 'package missing' error message is confusing
* [COOK-645] RHEL6/CentOS6 - mysql cookbook contains 'skip-federated' directive which is unsupported on MySQL 5.1

### v1.2.0

* [COOK-684] remove mysql_database LWRP

### v1.0.8:

* [COOK-633] ensure "cloud" attribute is available

### v1.0.7:

* [COOK-614] expose all mysql tunable settings in config
* [COOK-617] bind to private IP if available

### v1.0.6:

* [COOK-605] install mysql-client package on ubuntu/debian

### v1.0.5:

* [COOK-465] allow optional remote root connections to mysql
* [COOK-455] improve platform version handling
* externalize conf_dir attribute for easier cross platform support
* change datadir attribute to data_dir for consistency

### v1.0.4:

* fix regressions on debian platform
* [COOK-578] wrap root password in quotes
* [COOK-562] expose all tunables in my.cnf

License and Author
==================

Author:: Joshua Timberman (<joshua@opscode.com>)
Author:: AJ Christensen (<aj@opscode.com>)
Author:: Seth Chisamore (<schisamo@opscode.com>)

Copyright:: 2009-2011 Opscode, Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
