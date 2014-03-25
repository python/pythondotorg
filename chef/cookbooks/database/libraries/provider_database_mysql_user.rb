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

require File.join(File.dirname(__FILE__), 'provider_database_mysql')

class Chef
  class Provider
    class Database
      class MysqlUser < Chef::Provider::Database::Mysql
        include Chef::Mixin::ShellOut

        def load_current_resource
          Gem.clear_paths
          require 'mysql'
          @current_resource = Chef::Resource::DatabaseUser.new(@new_resource.name)
          @current_resource.username(@new_resource.name)
          @current_resource
        end

        def action_create
          unless exists?
            begin
              statement = "CREATE USER `#{@new_resource.username}`@`#{@new_resource.host}`"
              statement += " IDENTIFIED BY '#{@new_resource.password}'" if @new_resource.password
              db.query(statement)
              @new_resource.updated_by_last_action(true)
            ensure
              close
            end
          end
        end

        def action_drop
          if exists?
            begin
              db.query("DROP USER `#{@new_resource.username}`@`#{@new_resource.host}`")
              @new_resource.updated_by_last_action(true)
            ensure
              close
            end
          end
        end

        def action_grant
          begin
            # does password look like MySQL hex digest?
            # (begins with *, followed by 40 hexadecimal characters)
            if (/(\A\*[0-9A-F]{40}\z)/i).match(@new_resource.password) then
              password = filtered = "PASSWORD '#{$1}'"
            else
              password = "'#{@new_resource.password}'"
              filtered = '[FILTERED]'
            end
            grant_statement = "GRANT #{@new_resource.privileges.join(', ')} ON #{@new_resource.database_name && @new_resource.database_name != '*' ? "`#{@new_resource.database_name}`" : '*'}.#{@new_resource.table && @new_resource.table != '*' ? "`#{@new_resource.table}`" : '*'} TO `#{@new_resource.username}`@`#{@new_resource.host}` IDENTIFIED BY "
            with_grant_option = @new_resource.grant_option == true ? ' WITH GRANT OPTION ' : ''
            Chef::Log.info("#{@new_resource}: granting access with statement [#{grant_statement}#{filtered}]")
            db.query(grant_statement + password + with_grant_option)
            @new_resource.updated_by_last_action(true)
          ensure
            close
          end
        end

        private
        def exists?
          db.query("SELECT User,host from mysql.user WHERE User = '#{@new_resource.username}' AND host = '#{@new_resource.host}'").num_rows != 0
        end

      end
    end
  end
end
