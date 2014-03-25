#
# Cookbook Name:: postgresql
# Recipe:: client
#
# Author:: Joshua Timberman (<joshua@opscode.com>)
# Author:: Lamont Granquist (<lamont@opscode.com>)
# Copyright 2009-2011 Opscode, Inc.
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

if node['postgresql']['version'].to_f > 9.1 && platform_family?('ubuntu', 'debian')
  node.default['postgresql']['enable_pgdg_apt'] = true
end

if(node['postgresql']['enable_pgdg_apt'])
  include_recipe 'postgresql::apt_pgdg_postgresql'
end

if(node['postgresql']['enable_pgdg_yum'])
  include_recipe 'postgresql::yum_pgdg_postgresql'
end

node['postgresql']['client']['packages'].each do |pg_pack|

  package pg_pack

end
