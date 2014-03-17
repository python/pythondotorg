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

require 'chef/resource'

class Chef
  class Resource
    class Database < Chef::Resource

      def initialize(name, run_context=nil)
        super
        @resource_name = :database
        @database_name = name
        @allowed_actions.push(:create, :drop, :query)
        @action = :create
      end

      def database_name(arg=nil)
        set_or_return(
          :database_name,
          arg,
          :kind_of => String
        )
      end

      def connection(arg=nil)
        set_or_return(
          :connection,
          arg,
          :required => true
        )
      end

      def sql(arg=nil, &block)
        arg ||= block
        set_or_return(
          :sql,
          arg,
          :kind_of => [String, Proc]
        )
      end

      def sql_query
        if sql.kind_of?(Proc)
          sql.call
        else
          sql
        end
      end

      def template(arg=nil)
        set_or_return(
          :template,
          arg,
          :kind_of => String,
          :default => 'DEFAULT'
        )
      end

      def collation(arg=nil)
        set_or_return(
          :collation,
          arg,
          :kind_of => String
        )
      end

      def encoding(arg=nil)
        set_or_return(
          :encoding,
          arg,
          :kind_of => String,
          :default => 'DEFAULT'
        )
      end

      def tablespace(arg=nil)
        set_or_return(
          :tablespace,
          arg,
          :kind_of => String,
          :default => 'DEFAULT'
        )
      end

      def connection_limit(arg=nil)
        set_or_return(
          :connection_limit,
          arg,
          :kind_of => String,
          :default => '-1'
        )
      end

      def owner(arg=nil)
        set_or_return(
          :owner,
          arg,
          :kind_of => String
        )
      end
    end
  end
end
