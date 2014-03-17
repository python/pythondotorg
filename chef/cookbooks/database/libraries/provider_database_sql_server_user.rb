#
# Author:: Seth Chisamore (<schisamo@opscode.com>)
# Copyright:: Copyright (c) 2011 Opscode, Inc.
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

require File.join(File.dirname(__FILE__), 'provider_database_sql_server')

class Chef
  class Provider
    class Database
      class SqlServerUser < Chef::Provider::Database::SqlServer
        include Chef::Mixin::ShellOut

        def load_current_resource
          Gem.clear_paths
          require 'tiny_tds'
          @current_resource = Chef::Resource::DatabaseUser.new(@new_resource.name)
          @current_resource.username(@new_resource.name)
          @current_resource
        end

        def action_create
          begin
            unless exists?(:logins)
              db.execute("CREATE LOGIN [#{@new_resource.username}] WITH PASSWORD = '#{@new_resource.password}', CHECK_POLICY = OFF").do
              @new_resource.updated_by_last_action(true)
            end
            unless exists?(:users)
              if @new_resource.database_name
                Chef::Log.info("#{@new_resource} creating user in '#{@new_resource.database_name}' database context.")
                db.execute("USE [#{@new_resource.database_name}]").do
              else
                Chef::Log.info("#{@new_resource} database_name not provided, creating user in global context.")
              end
              db.execute("CREATE USER [#{@new_resource.username}] FOR LOGIN [#{@new_resource.username}]").do
              @new_resource.updated_by_last_action(true)
            end
          ensure
            close
          end
        end

        def action_drop
          begin
            if exists?(:users)
              db.execute("DROP USER [#{@new_resource.username}]").do
              @new_resource.updated_by_last_action(true)
            end
            if exists?(:logins)
              db.execute("DROP LOGIN [#{@new_resource.username}]").do
              @new_resource.updated_by_last_action(true)
            end
          ensure
            close
          end
        end

        def action_grant
          begin
            if @new_resource.password
              action_create
            end
            Chef::Application.fatal!('Please provide a database_name, SQL Server does not support global GRANT statements.') unless @new_resource.database_name
            grant_statement = "GRANT #{@new_resource.privileges.join(', ')} ON DATABASE::[#{@new_resource.database_name}] TO [#{@new_resource.username}]"
            Chef::Log.info("#{@new_resource} granting access with statement [#{grant_statement}]")
            db.execute("USE [#{@new_resource.database_name}]").do
            db.execute(grant_statement).do
            @new_resource.updated_by_last_action(true)
          ensure
            close
          end
        end

        def action_alter_roles
          begin
            if @new_resource.password
              action_create
            end
            Chef::Application.fatal!('Please provide a database_name, SQL Server does not support global GRANT statements.') unless @new_resource.database_name
            db.execute("USE [#{@new_resource.database_name}]").do
            @new_resource.sql_roles.each do | sql_role, role_action |
              alter_statement = "ALTER ROLE [#{sql_role}] #{role_action} MEMBER [#{@new_resource.username}]"
              Chef::Log.info("#{@new_resource} granting access with statement [#{alter_statement}]")
              db.execute(alter_statement).do
            end
            @new_resource.updated_by_last_action(true)
          ensure
            close
          end
        end

        private
        def exists?(type=:users)
          case type
          when :users
            table = "database_principals"
            if @new_resource.database_name
              Chef::Log.debug("#{@new_resource} searching for existing user in '#{@new_resource.database_name}' database context.")
              db.execute("USE [#{@new_resource.database_name}]").do
            end
          when :logins
            table = "server_principals"
          end

          result = db.execute("SELECT name FROM sys.#{table} WHERE name='#{@new_resource.username}'")
          result.each.any?
        end
      end
    end
  end
end
