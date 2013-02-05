#
# Author:: Joshua Timberman (<joshua@opscode.com>)
# Cookbook Name:: database
# Recipe:: ebs_backup
#
# Copyright 2009, Opscode, Inc.
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

begin
  aws = Chef::DataBagItem.load('aws', 'main')
  Chef::Log.info("Loaded AWS information from DataBagItem aws[#{aws['id']}]")
rescue
  Chef::Log.fatal("Could not find the 'main' item in the 'aws' data bag")
  raise
end

db_role = String.new
db_master_role = String.new
db_type = node[:database][:type]

search(:apps) do |app|
  db_role = app["database_#{db_type}_role"] & node.run_list.roles
  db_master_role = app["database_master_role"]
end

ebs_info = Chef::DataBagItem.load(:aws, "ebs_#{db_master_role}_#{node.chef_environment}")

gem_package "dbi"
gem_package "dbd-mysql"

directory "/mnt/aws-config" do
  mode 0700
  owner "root"
  group "root"
end

template "/mnt/aws-config/config" do
  source "aws_config.erb"
  variables(
    :access_key => aws['aws_access_key_id'],
    :secret_key => aws['aws_secret_access_key']
  )
  owner "root"
  group "root"
  mode 0600
end

git "/opt/ec2_mysql" do
  repository "git://github.com/jtimberman/ec2_mysql.git"
  reference "HEAD"
  action :sync
  not_if { ::FileTest.directory?("/opt/ec2_mysql/.git") }
end

%w{backup restore}.each do |file|
  template "/usr/local/bin/db-#{file}.sh" do
    source "ebs-db-#{file}.sh.erb"
    owner "root"
    group "root"
    mode 0700
    variables(
      :mysql_root_passwd => node['mysql']['server_root_password'],
      :mysql_device => node['mysql']['ebs_vol_dev'],
      :ebs_vol_id => ebs_info['volume_id']
    )
  end
end

if db_type == "master" && node.chef_environment == "production"
  template "/etc/cron.d/db-backup" do
    source "ebs-backup-cron.erb"
    owner "root"
    group "root"
    mode 0644
    backup false
  end
end
