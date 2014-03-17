#
# Cookbook Name:: postgresql
# Recipe:: config_pgtune
# Author:: David Crane (<davidc@donorschoose.org>)
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

#######
# Load the binaryround(value) method from libraries/default.rb
::Chef::Recipe.send(:include, Opscode::PostgresqlHelpers)

#######
# This recipe is based on Greg Smith's pgtune script (the Feb 1, 2012
# version at https://github.com/gregs1104/pgtune). Introduction: pgtune
# takes the wimpy default postgresql.conf and expands the database
# server to be as powerful as the hardware it's being deployed on.
#
# The default postgresql.conf aims at a system with approximately 128MB
# of RAM. This recipe recommends a baseline configuration in the right
# general range for a dedicated Postgresql system.
#
# This recipe takes three optional parameters that may be passed in as
# node['postgresql']['config_pgtune'] attributes:
#   * db_type -- Specifies database type as one of: dw, oltp,
#     web, mixed, desktop. If not specified, the default is mixed.
#   * max_connections -- Specifies number of maximum connections
#     expected. If not specified, it depends on database type.
#   * total_memory -- Specifies total system memory. If not specified,
#     it will be detected from the Ohai automatic attributes.
#
# Using those inputs, this recipe will compute and set the following
# node.default['postgresql']['config'] attributes:
#   * max_connections
#   * shared_buffers
#   * effective_cache_size
#   * work_mem
#   * maintenance_work_mem
#   * checkpoint_segments
#   * checkpoint_completion_target
#   * wal_buffers
#   * default_statistics_target
#
# This recipe deviates from the original pgtune script for 2 settings:
# shared_buffers is capped for large memory systems (which Greg
# mentioned in a TODO.rst) and wal_buffers will auto-tune starting with
# 9.1 (which is a feature that Greg built into Postgresql).

#######
# These are the workload characteristics of the five database types
# that can be specified as node['postgresql']['config_pgtune']['db_type']:
#
# dw -- Data Warehouse
#   * Typically I/O- or RAM-bound
#   * Large bulk loads of data
#   * Large complex reporting queries
#   * Also called "Decision Support" or "Business Intelligence"
#
# oltp -- Online Transaction Processing
#   * Typically CPU- or I/O-bound
#   * DB slightly larger than RAM to 1TB
#   * 20-40% small data write queries
#   * Some long transactions and complex read queries
#
# web -- Web Application
#   * Typically CPU-bound
#   * DB much smaller than RAM
#   * 90% or more simple queries
#
# mixed -- Mixed DW and OLTP characteristics
#   * A wide mixture of queries
#
# desktop -- Not a dedicated database
#   * A general workstation, perhaps for a developer

# Parse out db_type option, or use default.
db_type = 'mixed'

if (node['postgresql'].attribute?('config_pgtune') && node['postgresql']['config_pgtune'].attribute?('db_type'))
  db_type = node['postgresql']['config_pgtune']['db_type']
  if (!(["dw","oltp","web","mixed","desktop"].include?(db_type)))
    Chef::Application.fatal!([
        "Bad value (#{db_type})",
        "for node['postgresql']['config_pgtune']['db_type'] attribute.",
        "Valid values are one of dw, oltp, web, mixed, desktop."
      ].join(' '))
  end
end

# Parse out max_connections option, or use a value based on db_type.
con =
{ "web" => 200,
  "oltp" => 300,
  "dw" => 20,
  "mixed" => 80,
  "desktop" => 5
}.fetch(db_type)

if (node['postgresql'].attribute?('config_pgtune') && node['postgresql']['config_pgtune'].attribute?('max_connections'))
  max_connections = node['postgresql']['config_pgtune']['max_connections']
  if (max_connections.match(/\A[1-9]\d*\Z/) == nil)
    Chef::Application.fatal!([
        "Bad value (#{max_connections})",
        "for node['postgresql']['config_pgtune']['max_connections'] attribute.",
        "Valid values are non-zero integers only."
      ].join(' '))
  end
  con = max_connections.to_i
end

# Parse out total_memory option, or use value detected by Ohai.
total_memory = node['memory']['total']

# Override max_connections with a node attribute if DevOps desires.
# For example, on a system *not* dedicated to Postgresql.
if (node['postgresql'].attribute?('config_pgtune') && node['postgresql']['config_pgtune'].attribute?('total_memory'))
  total_memory = node['postgresql']['config_pgtune']['total_memory']
  if (total_memory.match(/\A[1-9]\d*kB\Z/) == nil)
    Chef::Application.fatal!([
        "Bad value (#{total_memory})",
        "for node['postgresql']['config_pgtune']['total_memory'] attribute.",
        "Valid values are non-zero integers followed by kB (e.g., 49416564kB)."
      ].join(' '))
  end
end

# Ohai reports node[:memory][:total] in kB, as in "921756kB"
mem = total_memory.split("kB")[0].to_i / 1024 # in MB

#######
# RAM-related settings computed as in Greg Smith's pgtune script.
# Remember that con and mem were either chosen above based on the
# db_type or the actual total memory, or were passed in attributes.

# (1) max_connections
#     Sets the maximum number of concurrent connections.
node.default['postgresql']['config']['max_connections'] = con

# The calculations for the next four settings would not be optimal
# for low memory systems. In that case, the calculation is skipped,
# leaving the built-in Postgresql settings, which are actually
# intended for those low memory systems.
if (mem >= 256)

  # (2) shared_buffers
  #     Sets the number of shared memory buffers used by the server.
  shared_buffers =
  { "web" => mem/4,
    "oltp" => mem/4,
    "dw" => mem/4,
    "mixed" => mem/4,
    "desktop" => mem/16
  }.fetch(db_type)

  # Robert Haas has advised to cap the size of shared_buffers based on
  # the memory architecture: 2GB on 32-bit and 8GB on 64-bit machines.
  # http://rhaas.blogspot.com/2012/03/tuning-sharedbuffers-and-walbuffers.html
  case node['kernel']['machine']
  when "i386" # 32-bit machines
    if shared_buffers > 2*1024
      shared_buffers = 2*1024
    end
  when "x86_64" # 64-bit machines
    if shared_buffers > 8*1024
      shared_buffers = 8*1024
    end
  end

  node.default['postgresql']['config']['shared_buffers'] = binaryround(shared_buffers*1024*1024)

  # (3) effective_cache_size
  #     Sets the planner's assumption about the size of the disk cache.
  #     That is, the portion of the kernel's disk cache that will be
  #     used for PostgreSQL data files.
  effective_cache_size =
  { "web" => mem * 3 / 4,
    "oltp" => mem * 3 / 4,
    "dw" => mem * 3 / 4,
    "mixed" => mem * 3 / 4,
    "desktop" => mem / 4
  }.fetch(db_type)

  node.default['postgresql']['config']['effective_cache_size'] = binaryround(effective_cache_size*1024*1024)

  # (4) work_mem
  #     Sets the maximum memory to be used for query workspaces.
  work_mem =
  { "web" => mem / con,
    "oltp" => mem / con,
    "dw" => mem / con / 2,
    "mixed" => mem / con / 2,
    "desktop" => mem / con / 6
  }.fetch(db_type)

  node.default['postgresql']['config']['work_mem'] = binaryround(work_mem*1024*1024)

  # (5) maintenance_work_mem
  #     Sets the maximum memory to be used for maintenance operations.
  #     This includes operations such as VACUUM and CREATE INDEX.
  maintenance_work_mem =
  { "web" => mem / 16,
    "oltp" => mem / 16,
    "dw" => mem / 8,
    "mixed" => mem / 16,
    "desktop" => mem / 16
  }.fetch(db_type)

  # Cap maintenence RAM at 1GB on servers with lots of memory
  if (maintenance_work_mem > 1*1024)
      maintenance_work_mem = 1*1024
  end

  node.default['postgresql']['config']['maintenance_work_mem'] = binaryround(maintenance_work_mem*1024*1024)

end

#######
# Checkpoint-related parameters that affect transaction rate and
# maximum tolerable recovery playback time.

# (6) checkpoint_segments
#     Sets the maximum distance in log segments between automatic WAL checkpoints.
checkpoint_segments =
{ "web" => 8,
  "oltp" => 16,
  "dw" => 64,
  "mixed" => 16,
  "desktop" => 3
}.fetch(db_type)

node.default['postgresql']['config']['checkpoint_segments'] = checkpoint_segments

# (7) checkpoint_completion_target
#     Time spent flushing dirty buffers during checkpoint, as fraction
#     of checkpoint interval.
checkpoint_completion_target =
{ "web" => "0.7",
  "oltp" => "0.9",
  "dw" => "0.9",
  "mixed" => "0.9",
  "desktop" => "0.5"
}.fetch(db_type)

node.default['postgresql']['config']['checkpoint_completion_target'] = checkpoint_completion_target

# (8) wal_buffers
#     Sets the number of disk-page buffers in shared memory for WAL.
# Starting with 9.1, wal_buffers will auto-tune if set to the -1 default.
# For 8.X and 9.0, it needed to be specified, which pgtune did as follows.
if node['postgresql']['version'].to_f < 9.1
  wal_buffers = 512 * checkpoint_segments
  # The pgtune seems to use 1kB units for wal_buffers
  node.default['postgresql']['config']['wal_buffers'] = binaryround(wal_buffers*1024)
else
  node.default['postgresql']['config']['wal_buffers'] = "-1"
end

# (9) default_statistics_target
#     Sets the default statistics target. This applies to table columns
#     that have not had a column-specific target set via
#     ALTER TABLE SET STATISTICS.
default_statistics_target =
{ "web" => 100,
  "oltp" => 100,
  "dw" => 500,
  "mixed" => 100,
  "desktop" => 100
}.fetch(db_type)

node.default['postgresql']['config']['default_statistics_target'] = default_statistics_target
