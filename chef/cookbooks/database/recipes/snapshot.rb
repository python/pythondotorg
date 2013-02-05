#
# Author:: AJ Christensen (<aj@opscode.com>)
# Cookbook Name:: database
# Recipe:: snapshot
#
# Copyright 2009-2010, Opscode, Inc.
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
include_recipe "aws"
include_recipe "xfs"

%w{ebs_vol_dev db_role app_environment username password aws_access_key_id aws_secret_access_key snapshots_to_keep volume_id}.collect do |key|
  Chef::Application.fatal!("Required db_snapshot configuration #{key} not found.", -47) unless node.db_snapshot.has_key? key
end

connection_info = {:host => localhost, :username => node.db_snapshot.username, :password => node.db_snapshot.password}

mysql_database "locking tables for #{node.db_snapshot.app_environment}" do
  connection connection_info
  sql "flush tables with read lock"
  action :query
end

execute "xfs freeze" do
  command "xfs_freeze -f #{node.db_snapshot.ebs_vol_dev}"
end

aws_ebs_volume "#{node.db_snapshot.db_role.first}_#{node.db_snapshot.app_environment}" do
  aws_access_key node.db_snapshot.aws_access_key_id
  aws_secret_access_key node.db_snapshot.aws_secret_access_key
  size 50
  device node.db_snapshot.ebs_vol_dev
  snapshots_to_keep node.db_snapshot.snapshots_to_keep
  action :snapshot
  volume_id node.db_snapshot.volume_id
  ignore_failure true # if this fails, continue to unfreeze and unlock
end

execute "xfs unfreeze" do
  command "xfs_freeze -u #{node.db_snapshot.ebs_vol_dev}"
end

mysql_database "unflushing tables for #{node.db_snapshot.app_environment}" do
  connection connection_info
  sql "unlock tables"
  action :query
end

aws_ebs_volume "#{node.db_snapshot.db_role.first}_#{node.db_snapshot.app_environment}" do
  action :prune
end
