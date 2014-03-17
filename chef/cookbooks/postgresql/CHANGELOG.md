postgresql Cookbook CHANGELOG
=============================
This file is used to list changes made in each version of the postgresql cookbook.


v3.3.4
------
Testing


v3.3.2
------
- Testing maintainer transfer to Heavywater with Opscode as collaborator


v3.3.0
------
### Bug
- **[COOK-3851](https://tickets.opscode.com/browse/COOK-3851)** - Postgresql: reload after config change does not pick up certain configuration changes
- **[COOK-3611](https://tickets.opscode.com/browse/COOK-3611)** - unix_socket_directory does not exists in 9.3
- **[COOK-2954](https://tickets.opscode.com/browse/COOK-2954)** - PostgreSQL installation ignores version attribute on CentOS >= 6


v3.2.0
------
- [COOK-3717] Pgdg repositories improvements
- [COOK-3756] Change postgresql.conf mode from 0600 to 0644


v3.1.0
------
### Improvement
- **[COOK-3685](https://tickets.opscode.com/browse/COOK-3685)** - Upgrade Repo Attributes for Postgresql 9.3
- **[COOK-3597](https://tickets.opscode.com/browse/COOK-3597)** - Fix implementation of `initdb_locale` attribute for RHEL
- **[COOK-3566](https://tickets.opscode.com/browse/COOK-3566)** - Give the user's rules more priority than the default ones in pg_hba
- **[COOK-3553](https://tickets.opscode.com/browse/COOK-3553)** - Remove automatic `apt-get update`

### Bug
- **[COOK-3611](https://tickets.opscode.com/browse/COOK-3611)** - Remove `unix_socket_directory` (it does not exists in 9.3)
- **[COOK-3599](https://tickets.opscode.com/browse/COOK-3599)** - Automatically add PGDG apt repo dependency on PostgreSQL version
- **[COOK-3555](https://tickets.opscode.com/browse/COOK-3555)** - Documentation Fix
- **[COOK-2383](https://tickets.opscode.com/browse/COOK-2383)** - Update Postgres version in attributes


v3.0.4
------
### Bug
- **[COOK-3173](https://tickets.opscode.com/browse/COOK-3173)** - Use :reload instead of :restart on conf changes
- **[COOK-2939](https://tickets.opscode.com/browse/COOK-2939)** - Fix RedHat support

v3.0.2
------
### Bug
- [COOK-3076]: postgresql::ruby recipe error when using pgdg repositories

v3.0.0
------
This is a backwards-incompatible release because the Pitti PPA is deprecated and the recipe removed, replaced with the PGDG apt repository.

### Bug
- [COOK-2571]: Create helper library for pg extension detection
- [COOK-2797]: Contrib extension contianing '-' fails to load.

### Improvement
- [COOK-2387]: Pitti Postgresql PPA is deprecated

### Task
- [COOK-3022]: update baseboxes in .kitchen.yml

v2.4.0
------
- [COOK-2163] - Dangerous "assign-postgres-password" in "recipes/server.rb" -- Can lock out dbadmin access
- [COOK-2390] - Recipes to auto-generate many postgresql.conf settings, following "initdb" and "pgtune"
- [COOK-2435] - Foodcritic fixes for postgresql cookbook
- [COOK-2476] - Installation into database of any contrib module extensions listed in a node attribute

v2.2.2
------
- [COOK-2232] -Provide PGDG yum repo to install postgresql 9.x on
  redhat-derived distributions

v2.2.0
------
- [COOK-2230] - Careful about Debian minor version numbers
- [COOK-2231] - Fix support for postgresql 9.x in server_redhat recipe
- [COOK-2238] - Postgresql recipe error in password check
- [COOK-2176] - PostgreSQL cookbook in Solo mode can cause "NoMethodError: undefined method `[]' for nil:NilClass"
- [COOK-2233] - Provide postgresql::contrib recipe to install useful server administration tools

v2.1.0
------
- [COOK-1872] - Allow latest PostgreSQL deb packages to be installed
- [COOK-1961] - Postgresql config file changes with every Chef run
- [COOK-2041] - Postgres cookbook no longer installs on OpenSuSE 11.4

v2.0.2
------
- [COOK-1406] - pg gem compile is unable to find libpq under Chef full stack (omnibus) installation

v2.0.0
------
This version is backwards incompatible with previous versions of the cookbook due to use of `platform_family`, and the refactored configuration files using node attributes. See README.md for details on how to modify configuration of PostgreSQL.

- [COOK-1508] - fix mixlib shellout error on SUSE
- [COOK-1744] - Add service enable & start
- [COOK-1779] - Don't run apt-get update and others in ruby recipe if pg is installed
- [COOK-1871] - Attribute driven configuration files for PostgreSQL
- [COOK-1900] - don't assume ssl on all postgresql 8.4+ installs
- [COOK-1901] - fail a chef-solo run when the postgres password
  attribute is not set

v1.0.0
------
**Important note for this release**

This version no longer installs Ruby bindings in the client recipe by default. Use the ruby recipe if you'd like the RubyGem. If you'd like packages for your distribution, use them in your application's specific cookbook/recipe, or modify the client packages attribute.

This resolves the following tickets.

- COOK-1011
- COOK-1534

The following issues are also resolved with this release.

- [COOK-1011] - Don't install postgresql packages during compile phase and remove pg gem installation
- [COOK-1224] - fix undefined variable on Debian
- [COOK-1462] - Add attribute for specifying listen address

v0.99.4
------
- [COOK-421] - config template is malformed
- [COOK-956] - add make package on ubuntu/debian

v0.99.2
------
- [COOK-916] - use < (with float) for version comparison.

v0.99.0
------
- Better support for Red Hat-family platforms
- Integration with database cookbook
- Make sure the postgres role is updated with a (secure) password
