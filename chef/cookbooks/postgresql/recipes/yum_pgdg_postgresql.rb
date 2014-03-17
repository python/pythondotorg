#
# Cookbook Name:: postgresql
# Recipe::yum_pgdg_postgresql
#
# Copyright 2013, DonorsChoose.org
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
# Load the pgdgrepo_rpm_info method from libraries/default.rb
::Chef::Recipe.send(:include, Opscode::PostgresqlHelpers)

######################################
# Install the "PostgreSQL RPM Building Project - Yum Repository" through
# the repo_rpm_url determined with pgdgrepo_rpm_info method from
# libraries/default.rb. The /etc/yum.repos.d/pgdg-*.repo
# will provide postgresql9X packages, but you may need to exclude
# postgresql packages from the repository of the distro in order to use
# PGDG repository properly. Conflicts will arise if postgresql9X does
# appear in your distro's repo and you want a more recent patch level.

repo_rpm_url, repo_rpm_filename, repo_rpm_package = pgdgrepo_rpm_info

# Download the PGDG repository RPM as a local file
remote_file "#{Chef::Config[:file_cache_path]}/#{repo_rpm_filename}" do
  source repo_rpm_url
  mode "0644"
end

# Install the PGDG repository RPM from the local file
# E.g., /etc/yum.repos.d/pgdg-91-centos.repo
package repo_rpm_package do
  provider Chef::Provider::Package::Rpm
  source "#{Chef::Config[:file_cache_path]}/#{repo_rpm_filename}"
  action :install
end
