#
# Cookbook Name:: ruby
# Definition:: ruby_symlinks
#
# Copyright 2010, FindsYou Limited
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

define :ruby_symlinks, :action => :create, :force => false, :path => '/usr/bin' do
  rv = params[:name].to_s
  rv = rv.slice(0..2).delete(".") if node[:platform] == "gentoo"

  %w( ruby irb erb ri testrb rdoc gem rake ).each do |name|
    path = File.join(params[:path], name)
    scope = self

    link path do
      to path + rv
      action params[:action]

      unless params[:force]
        not_if do
          if File.exists?(path) and not File.symlink?(path)
            scope.log "Not modifying non-symbolic-link #{path}"
            true
          end
        end
      end
    end
  end
end
