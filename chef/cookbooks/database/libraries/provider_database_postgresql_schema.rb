#
# Author:: Marco Betti (<m.betti@gmail.com>)
# Copyright:: Copyright (c) 2013 Opscode, Inc.
# License:: Apache License, Version 2.0
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

require File.join(File.dirname(__FILE__), 'provider_database_postgresql')

class Chef
  class Provider
    class Database
      class PostgresqlSchema < Chef::Provider::Database::Postgresql
        include Chef::Mixin::ShellOut

        def load_current_resource
          Gem.clear_paths
          require 'pg'
          @current_resource = Chef::Resource::PostgresqlDatabaseSchema.new(@new_resource.name)
          @current_resource.schema_name(@new_resource.schema_name)
          @current_resource
        end

        def action_create
          unless exists?
          begin
            if new_resource.owner
              db(@new_resource.database_name).query("CREATE SCHEMA \"#{@new_resource.schema_name}\" AUTHORIZATION \"#{@new_resource.owner}\"")
            else
              db(@new_resource.database_name).query("CREATE SCHEMA \"#{@new_resource.schema_name}\"")
            end
            @new_resource.updated_by_last_action(true)
          ensure
            close
          end
          end
        end

        def action_drop
          if exists?
            begin
              db(@new_resource.database_name).query("DROP SCHEMA \"#{@new_resource.schema_name}\"")
              @new_resource.updated_by_last_action(true)
            ensure
              close
            end
          end
        end

        private
        def exists?
          begin
            exists = db(@new_resource.database_name).query("SELECT schema_name FROM information_schema.schemata WHERE schema_name='#{@new_resource.schema_name}'").num_tuples != 0
          ensure
            close
          end
          exists
        end
      end
    end
  end
end
