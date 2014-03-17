database Cookbook CHANGELOG
=======================
This file is used to list changes made in each version of the database cookbook.


v2.0.0 (2014-02-25)
-------------------
[COOK-3441] database_user password argument should not be required


v1.6.0
------
### New Feature
- **[COOK-4009](https://tickets.opscode.com/browse/COOK-4009)** - Add PostgreSQL SCHEMA management capability

### Improvement
- **[COOK-3862](https://tickets.opscode.com/browse/COOK-3862)** - Improve database cookbook documentation


v1.5.2
------
### Improvement
- **[COOK-3716](https://tickets.opscode.com/browse/COOK-3716)** - Add ALTER SQL Server user roles


v1.5.0
------
### Improvement
- **[COOK-3546](https://tickets.opscode.com/browse/COOK-3546)** - Add connection parameters `:socket`
- **[COOK-1709](https://tickets.opscode.com/browse/COOK-1709)** - Add 'grant_option' parameter

v1.4.0
-------
### Bug
- [COOK-2074]: Regex in exists? check in `sql_server_database` resource should match for start and end of line
- [COOK-2561]: `mysql_database_user` can't set global grants

### Improvement

- [COOK-2075]: Support the collation attribute in the `database_sql_server` provider

v1.3.12
-------
- [COOK-850] - `postgresql_database_user` doesn't have example

v1.3.10
-------
- [COOK-2117] - undefined variable `grant_statement` in mysql user provider

v1.3.8
------
- [COOK-1896] - Escape command
- [COOK-2047] - Chef::Provider::Database::MysqlUser action :grant improperly quotes `username`@`host` string
- [COOK-2060] - Mysql::Error: Table '*.*' doesn't exist when privileges include SELECT and database/table attributes are nil
- [COOK-2062] - Remove backticks from database name when using wildcard

v1.3.6
------
- [COOK-1688] - fix typo in readme and add amazon linux to supported platforms

v1.3.4
------
- [COOK-1561] - depend on mysql 1.3.0+ explicitly
- depend on postgresql 1.0.0 explicitly

v1.3.2
------
- Update the version for release (oops)

v1.3.0
------
- [COOK-932] - Add mysql recipe to conveniently include mysql::ruby
- [COOK-1228] - database resource should be able to execute scripts on disk
- [COOK-1291] - make the snapshot retention policy less confusing
- [COOK-1401] - Allow to specify the collation of new databases
- [COOK-1534] - Add postgresql recipe to conveniently include postgresql::ruby

v1.2.0
------
- [COOK-970] - workaround for disk [re]naming on ubuntu 11.04+
- [COOK-1085] - check RUBY_VERSION and act accordingly for role
- [COOK-749] - localhost should be a string in snapshot recipe

v1.1.4
------
- [COOK-1062] - Databases: Postgres exists should close connection

v1.1.2
------
- [COOK-975] - Change arg='DEFAULT' to arg=nil, :default => 'DEFAULT'
- [COOK-964] - Add parentheses around connection hash in example

v1.1.0
------
- [COOK-716] - providers for PostgreSQL

v1.0.0
------
- [COOK-683] - added `database` and `database_user` resources
- [COOK-684] - MySQL providers
- [COOK-685] - SQL Server providers
- refactored - `database::master` and `database::snapshot` recipes to leverage new resources

v0.99.1
-------
- Use Chef 0.10's `node.chef_environment` instead of `node['app_environment']`.
