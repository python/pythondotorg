#
# Author:: Seth Chisamore (<schisamo@opscode.com>)
# Author:: Lamont Granquist (<lamont@opscode.com>)
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

require 'chef/provider'

class Chef
  class Provider
    class Database
      class Postgresql < Chef::Provider
        include Chef::Mixin::ShellOut

        def load_current_resource
          Gem.clear_paths
          require 'pg'
          @current_resource = Chef::Resource::Database.new(@new_resource.name)
          @current_resource.database_name(@new_resource.database_name)
          @current_resource
        end

        def action_create
          unless exists?
            begin
              encoding = @new_resource.encoding
              if encoding != "DEFAULT"
                encoding = "'#{@new_resource.encoding}'"
              end
              Chef::Log.debug("#{@new_resource}: Creating database #{new_resource.database_name}")
              create_sql = "CREATE DATABASE \"#{new_resource.database_name}\""
              create_sql += " TEMPLATE = #{new_resource.template}" if new_resource.template
              create_sql += " ENCODING = #{encoding}" if new_resource.encoding
              create_sql += " TABLESPACE = #{new_resource.tablespace}" if new_resource.tablespace
              create_sql += " LC_CTYPE = '#{new_resource.collation}' LC_COLLATE = '#{new_resource.collation}'" if new_resource.collation
              create_sql += " CONNECTION LIMIT = #{new_resource.connection_limit}" if new_resource.connection_limit
              create_sql += " OWNER = \"#{new_resource.owner}\"" if new_resource.owner
              Chef::Log.debug("#{@new_resource}: Performing query [#{create_sql}]")
              db("template1").query(create_sql)
              @new_resource.updated_by_last_action(true)
            ensure
              close
            end
          end
        end

        def action_drop
          if exists?
            begin
              Chef::Log.debug("#{@new_resource}: Dropping database #{new_resource.database_name}")
              db("template1").query("DROP DATABASE \"#{new_resource.database_name}\"")
              @new_resource.updated_by_last_action(true)
            ensure
              close
            end
          end
        end

        def action_query
          if exists?
            begin
              Chef::Log.debug("#{@new_resource}: Performing query [#{new_resource.sql_query}]")
              db(@new_resource.database_name).query(@new_resource.sql_query)
              Chef::Log.debug("#{@new_resource}: query [#{new_resource.sql_query}] succeeded")
              @new_resource.updated_by_last_action(true)
            ensure
              close
            end
          end
        end

        private

        def exists?
          begin
            Chef::Log.debug("#{@new_resource}: checking if database #{@new_resource.database_name} exists")
            ret = db("template1").query("SELECT * FROM pg_database where datname = '#{@new_resource.database_name}'").num_tuples != 0
            ret ? Chef::Log.debug("#{@new_resource}: database #{@new_resource.database_name} exists") :
                  Chef::Log.debug("#{@new_resource}: database #{@new_resource.database_name} does not exist")
          ensure
            close
          end
          ret
        end

        #
        # Specifying the database in the connection parameter for the postgres resource is not recommended.
        #
        # - action_create/drop/exists will use the "template1" database to do work by default.
        # - action_query will use the resource database_name.
        # - specifying a database in the connection will override this behavior
        #
        def db(dbname = nil)
          close if @db
          dbname = @new_resource.connection[:database] if @new_resource.connection[:database]
          host = @new_resource.connection[:host]
          port = @new_resource.connection[:port] || 5432
          user = @new_resource.connection[:username] || "postgres"
          Chef::Log.debug("#{@new_resource}: connecting to database #{dbname} on #{host}:#{port} as #{user}")
          password = @new_resource.connection[:password] || node[:postgresql][:password][:postgres]
          @db = ::PGconn.new(
            :host => host,
            :port => port,
            :dbname => dbname,
            :user => user,
            :password => password
          )
        end

        def close
          @db.close rescue nil
          @db = nil
        end

      end
    end
  end
end
