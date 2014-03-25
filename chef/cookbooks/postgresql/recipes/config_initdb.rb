#
# Cookbook Name:: postgresql
# Recipe:: config_initdb
# Author:: David Crane (<davidc@donorschoose.org>)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#######
# Load the locale_date_order() and select_default_timezone(tzdir)
# methods from libraries/default.rb
::Chef::Recipe.send(:include, Opscode::PostgresqlHelpers)

#######
# This recipe is derived from the setup_config() source code in the
# PostgreSQL initdb utility. It determines postgresql.conf settings that
# conform to the system's locale and timezone configuration, and also
# sets the error reporting and logging settings.
#
# See http://doxygen.postgresql.org/initdb_8c_source.html for the
# original initdb source code.
#
# By examining the system configuration, this recipe will set the
# following node.default['postgresql']['config'] attributes:
#
# - Locale and Formatting -
#   * datestyle
#   * lc_messages
#   * lc_monetary
#   * lc_numeric
#   * lc_time
#   * default_text_search_config
#
# - Timezone Conversion -
#   * log_timezone
#   * timezone
#
# In addition, this recipe will recommend the same error reporting and
# logging settings that initdb provided. These settings do differ from
# the PostgreSQL default settings, which would log to stderr only. The
# initdb settings rotate 7 days of log files named postgresql-Mon.log,
# etc. through these node.default['postgresql']['config'] attributes:
#
# - Where to Log -
#   * log_destination = 'stderr'
#   * log_directory = 'pg_log'
#   * log_filename = 'postgresql-%a.log'
#     (Default was: postgresql-%Y-%m-%d_%H%M%S.log)
#   * logging_collector = true # on
#     (Turned on to capture stderr logging and redirect into log files)
#     (Default was: false # off)
#   * log_rotation_age = 1d
#   * log_rotation_size = 0
#     (Default was: 10MB)
#   * log_truncate_on_rotation = true # on
#     (Default was: false # off)

#######
# Locale Configuration

# See libraries/default.rb for the locale_date_order() method.
node.default['postgresql']['config']['datestyle'] = "iso, #{locale_date_order()}"

# According to the locale(1) manpage, the locale settings are determined
# by environment variables according to the following precedence:
# LC_ALL > (LC_MESSAGES, LC_MONETARY, LC_NUMERIC, LC_TIME) > LANG.

node.default['postgresql']['config']['lc_messages'] =
  [ ENV['LC_ALL'], ENV['LC_MESSAGES'], ENV['LANG'] ].compact.first

node.default['postgresql']['config']['lc_monetary'] =
  [ ENV['LC_ALL'], ENV['LC_MONETARY'], ENV['LANG'] ].compact.first

node.default['postgresql']['config']['lc_numeric'] =
  [ ENV['LC_ALL'], ENV['LC_NUMERIC'], ENV['LANG'] ].compact.first

node.default['postgresql']['config']['lc_time'] =
  [ ENV['LC_ALL'], ENV['LC_TIME'], ENV['LANG'] ].compact.first

node.default['postgresql']['config']['default_text_search_config'] =
  case ENV['LANG']
  when /da_.*/
    'pg_catalog.danish'
  when /nl_.*/
    'pg_catalog.dutch'
  when /en_.*/
    'pg_catalog.english'
  when /fi_.*/
    'pg_catalog.finnish'
  when /fr_.*/
    'pg_catalog.french'
  when /de_.*/
    'pg_catalog.german'
  when /hu_.*/
    'pg_catalog.hungarian'
  when /it_.*/
    'pg_catalog.italian'
  when /no_.*/
    'pg_catalog.norwegian'
  when /pt_.*/
    'pg_catalog.portuguese'
  when /ro_.*/
    'pg_catalog.romanian'
  when /ru_.*/
    'pg_catalog.russian'
  when /es_.*/
    'pg_catalog.spanish'
  when /sv_.*/
    'pg_catalog.swedish'
  when /tr_.*/
    'pg_catalog.turkish'
  else
    nil
  end

#######
# Timezone Configuration

# Determine the name of the system's default timezone and specify node
# defaults for the postgresql.cof settings. If the timezone cannot be
# identified, do as initdb would do: leave it unspecified so PostgreSQL
# uses it's internal default of GMT.
tzdirpath = pg_TZDIR() # See libraries/default.rb
default_timezone = select_default_timezone(tzdirpath) # See libraries/default.rb
if !default_timezone.nil?
    node.default['postgresql']['config']['log_timezone'] = default_timezone
    node.default['postgresql']['config']['timezone'] = default_timezone
end

#######
# - Where to Log -
node.default['postgresql']['config']['log_destination'] = 'stderr'
node.default['postgresql']['config']['log_directory'] = 'pg_log'
node.default['postgresql']['config']['log_filename'] = 'postgresql-%a.log'
node.default['postgresql']['config']['logging_collector'] = true # on
node.default['postgresql']['config']['log_rotation_age'] = '1d'
node.default['postgresql']['config']['log_rotation_size'] = 0
node.default['postgresql']['config']['log_truncate_on_rotation'] = true # on
