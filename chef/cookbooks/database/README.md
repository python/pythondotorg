Database Cookbook
=================
The main highlight of this cookbook is the `database` and `database_user` resources for managing databases and database users in a RDBMS. Providers for MySQL, PostgreSQL and SQL Server are also provided, see usage documentation below.

This cookbook also contains recipes to configure mysql database masters and slaves and uses EBS for storage, integrating together with the application cookbook utilizing data bags for application related information. These recipes are written primarily to use MySQL and the Opscode mysql cookbook. Other RDBMS may be supported at a later date. This cookbook does not automatically restore database dumps, but does install tools to help with that.


Requirements
------------
Chef version 0.10.10+.

### Platforms
* Debian, Ubuntu
* Red Hat, CentOS, Scientific, Fedora, Amazon

### Cookbooks
The following Opscode cookbooks are dependencies:

* mysql
* postgresql
* xfs
* aws


Resources/Providers
-------------------
These resources aim to expose an abstraction layer for interacting with different RDBMS in a general way. Currently the cookbook ships with providers for MySQL, PostgreSQL and SQL Server. Please see specific usage in the __Example__ sections below. The providers use specific Ruby gems installed under Chef's Ruby environment to execute commands and carry out actions. These gems will need to be installed before the providers can operate correctly. Specific notes for each RDBS flavor:

- MySQL: leverages the `mysql` gem which is installed as part of the `mysql::ruby` recipe. You must declare `include_recipe "database::mysql"` to include this in your recipe.
- PostgreSQL: leverages the `pg` gem which is installed as part of the `postgresql::ruby` recipe. You must declare `include_recipe "database::postgresql"` to include this. 
- SQL Server: leverages the `tiny_tds` gem which is installed as part of the `sql_server::client` recipe.

This cookbook is not in charge of installing the Database Management System itself. Therefore, if you want to install MySQL, for instance, you should add `include_recipe "mysql::server"` in your recipe, or include `mysql::server` in the node run_list.

### database
Manage databases in a RDBMS. Use the proper shortcut resource depending on your RDBMS: `mysql_database`, `postgresql_database` or `sql_server_database`.

#### Actions
- :create: create a named database
- :drop: drop a named database
- :query: execute an arbitrary query against a named database

#### Attribute Parameters
- database_name: name attribute. Name of the database to interact with
- connection: hash of connection info. valid keys include :host, :port, :username, :password and :socket (only for MySQL DB*)
- sql: string of sql or a block that executes to a string of sql, which will be executed against the database. used by :query action only

\* The database cookbook uses the `mysql` gem, which uses the `real_connect()` function from mysql API to connect to the server.

> "The value of host may be either a host name or an IP address. If host is NULL or the string "localhost", a connection to the local host is assumed. For Windows, the client connects using a shared-memory connection, if the server has shared-memory connections enabled. Otherwise, TCP/IP is used. For Unix, the client connects using a Unix socket file. For local connections, you can also influence the type of connection to use with the MYSQL_OPT_PROTOCOL or MYSQL_OPT_NAMED_PIPE options to mysql_options(). The type of connection must be supported by the server. For a host value of "." on Windows, the client connects using a named pipe, if the server has named-pipe connections enabled. If named-pipe connections are not enabled, an error occurs."

If you set the `:host` key to "localhost" or if you leave it blank, a socket will be used. By default `real_connect()` function will look for socket in `/var/lib/mysql/mysql.sock`. If your socket file in non-default location - you can use :socket key to specify that location.

#### Providers
- `Chef::Provider::Database::Mysql`: shortcut resource `mysql_database`
- `Chef::Provider::Database::Postgresql`: shortcut resource `postgresql_database`
- `Chef::Provider::Database::SqlServer`: shortcut resource `sql_server_database`

#### Examples
```ruby
# Create a mysql database
mysql_database 'oracle_rules' do
  connection(
    :host     => 'localhost',
    :username => 'root',
    :password => node['mysql']['server_root_password']
  )
  action :create
end
```

```ruby
# Create a sql server database
sql_server_database 'mr_softie' do
  connection(
    :host     => '127.0.0.1',
    :port     => node['sql_server']['port'],
    :username => 'sa',
    :password => node['sql_server']['server_sa_password']
  )
  action :create
end
```

```ruby
# create a postgresql database
postgresql_database 'mr_softie' do
  connection(
    :host      => '127.0.0.1'
    :port      => 5432,
    :username  => 'postgres',
    :password  => node['postgresql']['password']['postgres']
  )
  action :create
end
```

```ruby
# create a postgresql database with additional parameters
postgresql_database 'mr_softie' do
  connection(
    :host     => '127.0.0.1',
    :port     => 5432,
    :username => 'postgres',
    :password => node['postgresql']['password']['postgres']
  )
  template 'DEFAULT'
  encoding 'DEFAULT'
  tablespace 'DEFAULT'
  connection_limit '-1'
  owner 'postgres'
  action :create
end
```

```ruby
# Externalize conection info in a ruby hash
mysql_connection_info = {
  :host     => 'localhost',
  :username => 'root',
  :password => node['mysql']['server_root_password']
}

sql_server_connection_info = {
  :host     => 'localhost',
  :port     => node['sql_server']['port'],
  :username => 'sa',
  :password => node['sql_server']['server_sa_password']
}

postgresql_connection_info = {
  :host     => '127.0.0.1',
  :port     => node['postgresql']['config']['port'],
  :username => 'postgres',
  :password => node['postgresql']['password']['postgres']
}



# Same create commands, connection info as an external hash
mysql_database 'foo' do
  connection mysql_connection_info
  action :create
end

sql_server_database 'foo' do
  connection sql_server_connection_info
  action     :create
end

postgresql_database 'foo' do
  connection postgresql_connection_info
  action     :create
end



# Create database, set provider in resource parameter
database 'bar' do
  connection mysql_connection_info
  provider   Chef::Provider::Database::Mysql
  action     :create
end

database 'bar' do
  connection sql_server_connection_info
  provider   Chef::Provider::Database::SqlServer
  action     :create
end

database 'bar' do
  connection postgresql_connection_info
  provider   Chef::Provider::Database::Postgresql
  action     :create
end



# Drop a database
mysql_database 'baz' do
  connection mysql_connection_info
  action    :drop
end



# Query a database
mysql_database 'flush the privileges' do
  connection mysql_connection_info
  sql        'flush privileges'
  action     :query
end



# Query a database from a sql script on disk
mysql_database 'run script' do
  connection mysql_connection_info
  sql { ::File.open('/path/to/sql_script.sql').read }
  action :query
end



# Vacuum a postgres database
postgresql_database 'vacuum databases' do
  connection      postgresql_connection_info
  database_table 'template1'
  sql 'VACUUM FULL VERBOSE ANALYZE'
  action :query
end
```

### database_user
Manage users and user privileges in a RDBMS. Use the proper shortcut resource depending on your RDBMS: `mysql_database_user`, `postgresql_database_user`, or `sql_server_database_user`.

#### Actions
- :create: create a user
- :drop: drop a user
- :grant: manipulate user privileges on database objects

#### Attribute Parameters
- username: name attribute. Name of the database user
- password: password for the user account
- database_name: Name of the database to interact with
- connection: hash of connection info. valid keys include :host, :port, :username, :password
- privileges: array of database privileges to grant user. used by the :grant action. default is :all
- grant_option: appends 'WITH GRANT OPTION' to grant statement. used by MySQL provider only. default is 'false'
- host: host where user connections are allowed from. used by MySQL provider only. default is 'localhost'
- table: table to grant privileges on. used by :grant action and MySQL provider only. default is '*' (all tables)

#### Providers
- `Chef::Provider::Database::MysqlUser`: shortcut resource `mysql_database_user`
- `Chef::Provider::Database::PostgresqlUser`: shortcut resource `postgresql_database_user`
- `Chef::Provider::Database::SqlServerUser`: shortcut resource`sql_server_database_user`

#### Examples

```ruby
# create connection info as an external ruby hash
mysql_connection_info = {
  :host     => 'localhost',
  :username => 'root',
  :password => node['mysql']['server_root_password']
}

postgresql_connection_info = {
  :host     => 'localhost',
  :port     => node['postgresql']['config']['port'],
  :username => 'postgres',
  :password => node['postgresql']['password']['postgres']
}

sql_server_connection_info = {
  :host     => 'localhost',
  :port     => node['sql_server']['port'],
  :username => 'sa',
  :password => node['sql_server']['server_sa_password']
}



# Create a mysql user but grant no privileges
mysql_database_user 'disenfranchised' do
  connection mysql_connection_info
  password   'super_secret'
  action     :create
end



# Do the same but pass the provider to the database resource
database_user 'disenfranchised' do
  connection mysql_connection_info
  password   'super_secret'
  provider   Chef::Provider::Database::MysqlUser
  action     :create
end



# Create a postgresql user but grant no privileges
postgresql_database_user 'disenfranchised' do
  connection postgresql_connection_info
  password   'super_secret'
  action     :create
end



# Do the same but pass the provider to the database resource
database_user 'disenfranchised' do
  connection postgresql_connection_info
  password   'super_secret'
  provider   Chef::Provider::Database::PostgresqlUser
  action     :create
end



# Create a sql server user but grant no privileges
sql_server_database_user 'disenfranchised' do
  connection sql_server_connection_info
  password   'super_secret'
  action     :create
end



# Drop a mysql user
mysql_database_user 'foo_user' do
  connection mysql_connection_info
  action     :drop
end



# Bulk drop sql server users
%w(disenfranchised foo_user).each do |user|
  sql_server_database_user user do
    connection sql_server_connection_info
    action     :drop
  end
end



# Grant SELECT, UPDATE, and INSERT privileges to all tables in foo db from all hosts
mysql_database_user 'foo_user' do
  connection    mysql_connection_info
  password      'super_secret'
  database_name 'foo'
  host          '%'
  privileges    [:select,:update,:insert]
  action        :grant
end



# Grant all privileges on all databases/tables from localhost
mysql_database_user 'super_user' do
  connection mysql_connection_info
  password   'super_secret'
  action     :grant
end



# Grant all privileges on all tables in foo db
postgresql_database_user 'foo_user' do
  connection    postgresql_connection_info
  database_name 'foo'
  privileges    [:all]
  action        :grant
end

# grant select,update,insert privileges to all tables in foo db
sql_server_database_user 'foo_user' do
  connection    sql_server_connection_info
  password      'super_secret'
  database_name 'foo'
  privileges    [:select,:update,:insert]
  action        :grant
end
```


Recipes
-------
### ebs_volume
*Note*: This recipe does not currently work on RHEL platforms due to the xfs cookbook not supporting RHEL yet.

Loads the aws information from the data bag. Searches the applications data bag for the database master or slave role and checks that role is applied to the node. Loads the EBS information and the master information from data bags. Uses the aws cookbook LWRP, `aws_ebs_volume` to manage the volume.

On a master node:
- if we have an ebs volume already as stored in a data bag, attach it
- if we don't have the ebs information then create a new one and attach it
- store the volume information in a data bag via a ruby block

On a slave node:
- use the master volume information to generate a snapshot
- create the new volume from the snapshot and attach it

Also on a master node, generate some configuration for running a snapshot via `chef-solo` from cron.

On a new filesystem volume, create as XFS, then mount it in `/mnt`, and also bind-mount it to the mysql data directory (default `/var/lib/mysql`).

### master
This recipe no longer loads AWS specific information, and the database position for replication is no longer stored in a databag because the client might not have permission to write to the databag item. This may be handled in a different way at a future date.

Searches the apps databag for applications, and for each one it will check that the specified database master role is set in both the databag and applied to the node's run list. Then, retrieves the passwords for `root`, `repl` and `debian` users and saves them to the node attributes. If the passwords are not found in the databag, it prints a message that they'll be generated by the mysql cookbook.

Then it adds the application databag database settings to a hash, to use later.

Then it will iterate over the databases and create them with the `mysql_database` resource while adding privileges for application specific database users using the `mysql_database_user` resource.

### slave
_TODO_: Retrieve the master status from a data bag, then start replication using a ruby block. The replication status needs to be handled in some other way for now since the master recipe above doesn't actually set it in the databag anymore.

### snapshot
Run via Chef Solo. Retrieves the db snapshot configuration from the specified JSON file. Uses the `mysql_database` resource to lock and unlock tables, and does a filesystem freeze and EBS snapshot.


Deprecated Recipes
------------------
The following recipe is considered deprecated. It is kept for reference purposes.

### ebs_backup
Older style of doing mysql snapshot and replication using Adam Jacob's [ec2_mysql](http://github.com/adamhjk/ec2_mysql) script and library.


Data Bags
---------
This cookbook uses the apps data bag item for the specified application; see the `application` cookbook's README.md. It also creates data bag items in a bag named 'aws' for storing volume information. In order to interact with EC2, it expects aws to have a main item:

```javascript
{
  "id": "main",
  "ec2_private_key": "private key as a string",
  "ec2_cert": "certificate as a string",
  "aws_account_id": "",
  "aws_secret_access_key": "",
  "aws_access_key_id": ""
}
```

Note: with the Open Source Chef Server, the server using the database recipes must be an admin client or it will not be able to create data bag items. You can modify whether the client is admin by editing it with knife.

    knife client edit <client_name>
    {
      ...
      "admin": true
      ...
    }

This is not required if the Chef Server is Opscode Hosted Chef, instead use the ACL feature to modify access for the node to be able to update the data bag.


Usage
-----
Aside from the application data bag (see the README in the application cookbook), create a role for the database master. Use a `role.rb` in your chef-repo, or create the role directly with knife.

```javascript
{
  "name": "my_app_database_master",
  "chef_type": "role",
  "json_class": "Chef::Role",
  "default_attributes": {},
  "description": "",
  "run_list": [
    "recipe[mysql::server]",
    "recipe[database::master]"
  ],
  "override_attributes": {}
}
```

Create a `production` environment. This is also used in the `application` cookbook.

```javascript
{
  "name": "production",
  "description": "",
  "cookbook_versions": {},
  "json_class": "Chef::Environment",
  "chef_type": "environment",
  "default_attributes": {},
  "override_attributes": {}
}
```

The cookbook `my_app_database` is recommended to set up any application specific database resources such as configuration templates, trending monitors, etc. It is not required, but you would need to create it separately in `site-cookbooks`. Add it to the `my_app_database_master` role.

License & Authors
-----------------
- Author:: Adam Jacob (<adam@opscode.com>)
- Author:: Joshua Timberman (<joshua@opscode.com>)
- Author:: AJ Christensen (<aj@opscode.com>)
- Author:: Seth Chisamore (<schisamo@opscode.com>)
- Author:: Lamont Granquist (<lamont@opscode.com>)

```text
Copyright 2009-2013, Opscode, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
