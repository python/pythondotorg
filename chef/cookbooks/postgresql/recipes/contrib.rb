#
# Cookbook Name:: postgresql
# Recipe:: contrib
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

include_recipe "postgresql::server"

# Install the PostgreSQL contrib package(s) from the distribution,
# as specified by the node attributes.
node['postgresql']['contrib']['packages'].each do |pg_pack|

  package pg_pack

end

# Install PostgreSQL contrib extentions into the template1 database,
# as specified by the node attributes.
if (node['postgresql']['contrib'].attribute?('extensions'))
  node['postgresql']['contrib']['extensions'].each do |pg_ext|
    bash "install-#{pg_ext}-extension" do
      user 'postgres'
      code <<-EOH
        echo 'CREATE EXTENSION IF NOT EXISTS "#{pg_ext}";' | psql -d template1
      EOH
      action :run
      ::Chef::Resource.send(:include, Opscode::PostgresqlHelpers)
      not_if {extension_installed?(pg_ext)}
    end
  end
end
