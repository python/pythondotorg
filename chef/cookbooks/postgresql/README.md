Description
===========

Installs and configures PostgreSQL as a client or a server.

Requirements
============

## Platforms

* Debian, Ubuntu
* Red Hat/CentOS/Scientific (6.0+ required) - "EL6-family"
* Fedora
* SUSE

Tested on:

* Ubuntu 10.04, 11.10, 12.04
* Red Hat 6.1, Scientific 6.1, CentOS 6.3

## Cookbooks

Requires Opscode's `openssl` cookbook for secure password generation.

Requires a C compiler and development headers in order to build the
`pg` RubyGem to provide Ruby bindings in the `ruby` recipe.

Opscode's `build-essential` cookbook provides this functionality on
Debian, Ubuntu, and EL6-family.

While not required, Opscode's `database` cookbook contains resources
and providers that can interact with a PostgreSQL database. This
cookbook is a dependency of database.

Attributes
==========

The following attributes are set based on the platform, see the
`attributes/default.rb` file for default values.

* `node['postgresql']['version']` - version of postgresql to manage
* `node['postgresql']['dir']` - home directory of where postgresql
  data and configuration lives.

* `node['postgresql']['client']['packages']` - An array of package names
  that should be installed on "client" systems.
* `node['postgresql']['server']['packages']` - An array of package names
  that should be installed on "server" systems.
* `node['postgresql']['server']['config_change_notify']` - Type of
  notification triggered when a config file changes.
* `node['postgresql']['contrib']['packages']` - An array of package names
  that could be installed on "server" systems for useful sysadmin tools.

* `node['postgresql']['enable_pgdg_apt']` - Whether to enable the apt repo
  by the PostgreSQL Global Development Group, which contains newer versions
  of PostgreSQL.

* `node['postgresql']['enable_pgdg_yum']` - Whether to enable the yum repo
  by the PostgreSQL Global Development Group, which contains newer versions
  of PostgreSQL.

* `node['postgresql']['initdb_locale']` - Sets the default locale for the
  database cluster. If this attribute is not specified, the locale is
  inherited from the environment that initdb runs in. Sometimes you must
  have a system locale that is not what you want for your database cluster,
  and this attribute addresses that scenario. Valid only for EL-family
  distros (RedHat/Centos/etc.).

The following attributes are generated in
`recipe[postgresql::server]`.

* `node['postgresql']['password']['postgres']` - randomly generated
  password by the `openssl` cookbook's library.
  (TODO: This is broken, as it disables the password.)

Configuration
-------------

The `postgresql.conf` and `pg_hba.conf` files are dynamically
generated from attributes. Each key in `node['postgresql']['config']`
is a postgresql configuration directive, and will be rendered in the
config file. For example, the attribute:

    node['postgresql']['config']['listen_addresses'] = 'localhost'

Will result in the following line in the `postgresql.conf` file:

    listen_addresses = 'localhost'

The attributes file contains default values for Debian and RHEL
platform families (per the `node['platform_family']`). These defaults
have disparity between the platforms because they were originally
extracted from the postgresql.conf files in the previous version of
this cookbook, which differed in their default config. The resulting
configuration files will be the same as before, but the content will
be dynamically rendered from the attributes. The helpful commentary
will no longer be present. You should consult the PostgreSQL
documentation for specific configuration details.

See __Recipes__ `config_initdb` and `config_pgtune` below to
auto-generate many postgresql.conf settings.

For values that are "on" or "off", they should be specified as literal
`true` or `false`. String values will be used with single quotes. Any
configuration option set to the literal `nil` will be skipped
entirely. All other values (e.g., numeric literals) will be used as
is. So for example:

    node.default['postgresql']['config']['logging_collector'] = true
    node.default['postgresql']['config']['datestyle'] = 'iso, mdy'
    node.default['postgresql']['config']['ident_file'] = nil
    node.default['postgresql']['config']['port] = 5432

Will result in the following config lines:

    logging_collector = 'on'
    datestyle = 'iso,mdy'
    port = 5432

(no line printed for `ident_file` as it is `nil`)

Note that the `unix_socket_directory` configuration was renamed to
`unix_socket_directories` in Postgres 9.3 so make sure to use the
`node['postgresql']['unix_socket_directories']` attribute instead of
`node['postgresql']['unix_socket_directory']`.

The `pg_hba.conf` file is dynamically generated from the
`node['postgresql']['pg_hba']` attribute. This attribute must be an
array of hashes, each hash containing the authorization data. As it is
an array, you can append to it in your own recipes. The hash keys in
the array must be symbols. Each hash will be written as a line in
`pg_hba.conf`. For example, this entry from
`node['postgresql']['pg_hba']`:

    {:comment => '# Optional comment',
    :type => 'local', :db => 'all', :user => 'postgres', :addr => nil, :method => 'md5'}

Will result in the following line in `pg_hba.conf`:

    # Optional comment
    local   all             postgres                                md5

Use `nil` if the CIDR-ADDRESS should be empty (as above).
Don't provide a comment if none is desired in the `pg_hba.conf` file.

Note that the following authorization rule is supplied automatically by
the cookbook template. The cookbook needs this to execute SQL in the
PostgreSQL server without supplying the clear-text password (which isn't
known by the cookbook). Therefore, your `node['postgresql']['pg_hba']`
attributes don't need to specify this authorization rule:

    # "local" is for Unix domain socket connections only
    local   all             all                                     ident

(By the way, the template uses `peer` instead of `ident` for PostgreSQL-9.1
and above, which has the same effect.)

Recipes
=======

default
-------

Includes the client recipe.

client
------

Installs the packages defined in the
`node['postgresql']['client']['packages']` attribute.

ruby
----

**NOTE** This recipe may not currently work when installing Chef with
  the
  ["Omnibus" full stack installer](http://opscode.com/chef/install) on
  some platforms due to an incompatibility with OpenSSL. See
  [COOK-1406](http://tickets.opscode.com/browse/COOK-1406). You can
  build from source into the Chef omnibus installation to work around
  this issue.

Install the `pg` gem under Chef's Ruby environment so it can be used
in other recipes. The build-essential packages and postgresql client
packages will be installed during the compile phase, so that the
native extensions of `pg` can be compiled.

server
------

Includes the `server_debian` or `server_redhat` recipe to get the
appropriate server packages installed and service managed. Also
manages the configuration for the server:

* generates a strong default password (via `openssl`) for `postgres`
  (TODO: This is broken, as it disables the password.)
* sets the password for postgres
* manages the `postgresql.conf` file.
* manages the `pg_hba.conf` file.

server\_debian
--------------

Installs the postgresql server packages and sets up the service. You
should include the `postgresql::server` recipe, which will include
this on Debian platforms.

server\_redhat
--------------

Manages the postgres user and group (with UID/GID 26, per RHEL package
conventions), installs the postgresql server packages, initializes the
database, and manages the postgresql service. You should include the
`postgresql::server` recipe, which will include this on RHEL/Fedora
platforms.

config\_initdb
--------------

Takes locale and timezone settings from the system configuration.
This recipe creates `node.default['postgresql']['config']` attributes
that conform to the system's locale and timezone. In addition, this
recipe creates the same error reporting and logging settings that
`initdb` provided: a rotation of 7 days of log files named
postgresql-Mon.log, etc.

The default attributes created by this recipe are easy to override with
normal attributes because of Chef attribute precedence. For example,
suppose a DBA wanted to keep log files indefinitely, rolling over daily
or when growing to 10MB. The Chef installation could include the
`postgresql::config_initdb` recipe for the locale and timezone settings,
but customize the logging settings with these node JSON attributes:

    "postgresql": {
      "config": {
        "log_rotation_age": "1d",
        "log_rotation_size": "10MB",
        "log_filename": "postgresql-%Y-%m-%d_%H%M%S.log"
      }
    }

Credits: This `postgresql::config_initdb` recipe is based on algorithms
in the [source code](http://doxygen.postgresql.org/initdb_8c_source.html)
for the PostgreSQL `initdb` utility.

config\_pgtune
--------------

Performance tuning.
Takes the wimpy default postgresql.conf and expands the database server
to be as powerful as the hardware it's being deployed on. This recipe
creates a baseline configuration of `node.default['postgresql']['config']`
attributes in the right general range for a dedicated Postgresql system.
Most installations won't need additional performance tuning.

The only decision you need to make is to choose a `db_type` from the
following database workloads. (See the recipe code comments for more
detailed descriptions.)

 * "dw" -- Data Warehouse
 * "oltp" -- Online Transaction Processing
 * "web" -- Web Application
 * "mixed" -- Mixed DW and OLTP characteristics
 * "desktop" -- Not a dedicated database

This recipe uses a performance model with three input parameters.
These node attributes are completely optional, but it is obviously
important to choose the `db_type` correctly:

 * `node['postgresql']['config_pgtune']['db_type']` --
   Specifies database type from the list of five choices above.
   If not specified, the default is "mixed".

 * `node['postgresql']['config_pgtune']['max_connections']` --
   Specifies maximum number of connections expected.
   If not specified, it depends on database type:
   "web":200, "oltp":300, "dw":20, "mixed":80, "desktop":5

 * `node['postgresql']['config_pgtune']['total_memory']` --
   Specifies total system memory in kB. (E.g., "49416564kB".)
   If not specified, it will be taken from Ohai automatic attributes.
   This could be used to tune a system that isn't a dedicated database.

The default attributes created by this recipe are easy to override with
normal attributes because of Chef attribute precedence. For example, if
you are running application benchmarks to try different buffer cache
sizes, you would experiment with this node JSON attribute:

    "postgresql": {
      "config": {
        "shared_buffers": "3GB"
      }
    }

Note that the recipe uses `max_connections` in its computations. If
you want to override that setting, you should specify
`node['postgresql']['config_pgtune']['max_connections']` instead of
`node['postgresql']['config']['max_connections']`.

Credits: This `postgresql::config_pgtune` recipe is based on the
[pgtune python script](https://github.com/gregs1104/pgtune)
developed by
[Greg Smith](http://notemagnet.blogspot.com/2008/11/automating-initial-postgresqlconf.html)
and
[other pgsql-hackers](http://www.postgresql.org/message-id/491C6CDC.8090506@agliodbs.com).

contrib
-------

Installs the packages defined in the
`node['postgresql']['contrib']['packages']` attribute. The contrib
directory of the PostgreSQL distribution includes porting tools,
analysis utilities, and plug-in features that database engineers often
require. Some (like `pgbench`) are executable. Others (like
`pg_buffercache`) would need to be installed into the database.

Also installs any contrib module extensions defined in the
`node['postgresql']['contrib']['extensions']` attribute. These will be
available in any subsequently created databases in the cluster, because
they will be installed into the `template1` database using the
`CREATE EXTENSION` command. For example, it is often necessary/helpful
for problem troubleshooting and maintenance planning to install the
views and functions in these [standard instrumentation extensions]
(http://www.postgresql.org/message-id/flat/4DC32600.6080900@pgexperts.com#4DD3D6C6.5060006@2ndquadrant.com):

    node['postgresql']['contrib']['extensions'] = [
      "pageinspect",
      "pg_buffercache",
      "pg_freespacemap",
      "pgrowlocks",
      "pg_stat_statements",
      "pgstattuple"
    ]

Note that the `pg_stat_statements` view only works if `postgresql.conf`
loads its shared library, which can be done with this node attribute:

    node['postgresql']['config']['shared_preload_libraries'] = 'pg_stat_statements'

apt\_pgdg\_postgresql
----------------------

Enables the PostgreSQL Global Development Group yum repository
maintained by Devrim G&#252;nd&#252;z for updated PostgreSQL packages.
(The PGDG is the groups that develops PostgreSQL.)
Automatically included if the `node['postgresql']['enable_pgdg_apt']`
attribute is true. Also set the
`node['postgresql']['client']['packages']` and
`node['postgresql']['server]['packages']` to the list of packages to
use from this repository, and set the `node['postgresql']['version']`
attribute to the version to use (e.g., "9.2").

yum\_pgdg\_postgresql
---------------------

Enables the PostgreSQL Global Development Group yum repository
maintained by Devrim G&#252;nd&#252;z for updated PostgreSQL packages.
(The PGDG is the groups that develops PostgreSQL.)
Automatically included if the `node['postgresql']['enable_pgdg_yum']`
attribute is true. Also use `override_attributes` to set a number of
values that will need to have embedded version numbers. For example:

    node['postgresql']['enable_pgdg_yum'] = true
    node['postgresql']['version'] = "9.2"
    node['postgresql']['dir'] = "/var/lib/pgsql/9.2/data"
    node['postgresql']['client']['packages'] = ["postgresql92", "postgresql92-devel"]
    node['postgresql']['server']['packages'] = ["postgresql92-server"]
    node['postgresql']['server']['service_name'] = "postgresql-9.2"
    node['postgresql']['contrib']['packages'] = ["postgresql92-contrib"]

You may set `node['postgresql']['pgdg']['repo_rpm_url']` attributes
to pick up recent [PGDG repo packages](http://yum.postgresql.org/repopackages.php).

Resources/Providers
===================

See the [database](http://community.opscode.com/cookbooks/database)
for resources and providers that can be used for managing PostgreSQL
users and databases.

Usage
=====

On systems that need to connect to a PostgreSQL database, add to a run
list `recipe[postgresql]` or `recipe[postgresql::client]`.

On systems that should be PostgreSQL servers, use
`recipe[postgresql::server]` on a run list. This recipe does set a
password for the `postgres` user.
If you're using `chef server`, if the attribute
`node['postgresql']['password']['postgres']` is not found,
the recipe generates a random password and performs a node.save.
(TODO: This is broken, as it disables the password.)
If you're using `chef-solo`, you'll need
to set the attribute `node['postgresql']['password']['postgres']` in
your node's `json_attribs` file or in a role.

On Debian family systems, SSL will be enabled, as the packages on
Debian/Ubuntu also generate the SSL certificates. If you use another
platform and wish to use SSL in postgresql, then generate your SSL
certificates and distribute them in your own cookbook, and set the
`node['postgresql']['config']['ssl']` attribute to true in your
role/cookboook/node.

On server systems, the postgres server is restarted when a configuration
file changes.  This can be changed to reload only by setting the
following attribute:

    node['postgresql']['server']['config_change_notify'] = :reload

Chef Solo Note
==============

The following node attribute is stored on the Chef Server when using
`chef-client`. Because `chef-solo` does not connect to a server or
save the node object at all, to have the password persist across
`chef-solo` runs, you must specify them in the `json_attribs` file
used. For Example:

    {
      "postgresql": {
        "password": {
          "postgres": "iloverandompasswordsbutthiswilldo"
        }
      },
      "run_list": ["recipe[postgresql::server]"]
    }

That should actually be the "encrypted password" instead of cleartext,
so you should generate it as an md5 hash using the PostgreSQL algorithm.

* You could copy the md5-hashed password from an existing postgres
database if you have `postgres` access and want to use the same password:<br>
`select * from pg_shadow where usename='postgres';`
* You can run this from any postgres database session to use a new password:<br>
`select 'md5'||md5('iloverandompasswordsbutthiswilldo'||'postgres');`
* You can run this from a linux commandline:<br>
`echo -n 'iloverandompasswordsbutthiswilldo''postgres' | openssl md5 | sed -e 's/.* /md5/'`

License and Author
==================

- Author:: Joshua Timberman (<joshua@opscode.com>)
- Author:: Lamont Granquist (<lamont@opscode.com>)
- Author:: Chris Roberts (<chrisroberts.code@gmail.com>)
- Author:: David Crane (<davidc@donorschoose.org>)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
