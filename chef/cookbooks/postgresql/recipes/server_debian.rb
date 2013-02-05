#
# Cookbook Name:: postgresql
# Recipe:: server
#
# Author:: Joshua Timberman (<joshua@opscode.com>)
# Author:: Lamont Granquist (<lamont@opscode.com>)#
# Copyright 2009-2011, Opscode, Inc.
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

include_recipe "postgresql::client"

case node[:postgresql][:version]
when "8.3"
  node.default[:postgresql][:ssl] = "off"
else # > 8.3
  node.default[:postgresql][:ssl] = "true"
end

package "postgresql"

# use /mnt so we have access to a larger volume for psql databases on amazon
directory "/mnt/data/postgresql/#{node['postgresql']['version']}/main" do
  owner "postgres"
  group "postgres"
  mode "0700"
  recursive true
end
execute "copy_postgres_to_mnt" do
  command "cp -R -p /var/lib/postgresql/#{node['postgresql']['version']}/main/* /mnt/data/postgresql/#{node['postgresql']['version']}/main/"
  creates "/mnt/data/postgresql/#{node['postgresql']['version']}/main/PG_VERSION"
  action :run
  user "postgres"
  group "postgres"
end

service "postgresql" do
  case node['platform']
  when "ubuntu"
    case
    when node['platform_version'].to_f <= 10.04
      service_name "postgresql-#{node['postgresql']['version']}"
    else
      service_name "postgresql"
    end
  when "debian"
    case
    when platform_version.to_f <= 5.0
      service_name "postgresql-#{node['postgresql']['version']}"
    when platform_version =~ /squeeze/
      service_name "postgresql"
    else
      service_name "postgresql"
    end
  end
  supports :restart => true, :status => true, :reload => true
  action :nothing
end

template "#{node[:postgresql][:dir]}/postgresql.conf" do
  source "debian.postgresql.conf.erb"
  owner "postgres"
  group "postgres"
  mode 0600
  notifies :restart, resources(:service => "postgresql")
end
