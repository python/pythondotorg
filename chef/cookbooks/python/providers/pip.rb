#
# Author:: Seth Chisamore <schisamo@opscode.com>
# Cookbook Name:: python
# Provider:: pip
#
# Copyright:: 2011, Opscode, Inc <legal@opscode.com>
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

require 'chef/mixin/shell_out'
require 'chef/mixin/language'
include Chef::Mixin::ShellOut

# the logic in all action methods mirror that of 
# the Chef::Provider::Package which will make
# refactoring into core chef easy

action :install do
  # If we specified a version, and it's not the current version, move to the specified version
  if @new_resource.version != nil && @new_resource.version != @current_resource.version
    install_version = @new_resource.version
  # If it's not installed at all, install it
  elsif @current_resource.version == nil
    install_version = candidate_version
  end

  # Set the timeout (units in seconds)
  timeout = 900
  if @new_resource.timeout
    timeout = @new_resource.timeout
  end
  
  if install_version
    Chef::Log.info("Installing #{@new_resource} version #{install_version}")
    status = install_package(@new_resource.package_name, install_version, timeout)
    if status
      @new_resource.updated_by_last_action(true)
    end
  end
end

action :upgrade do
  # Set the timeout (units in seconds)
  timeout = 900
  if @new_resource.timeout
    timeout = @new_resource.timeout
  end

  if @current_resource.version != candidate_version
    orig_version = @current_resource.version || "uninstalled"
    Chef::Log.info("Upgrading #{@new_resource} version from #{orig_version} to #{candidate_version}")
    status = upgrade_package(@new_resource.package_name, candidate_version, timeout)
    if status
      @new_resource.updated_by_last_action(true)
    end
  end
end

action :remove do
  # Set the timeout (units in seconds)
  timeout = 900
  if @new_resource.timeout
    timeout = @new_resource.timeout
  end

  if removing_package?
    Chef::Log.info("Removing #{@new_resource}")
    remove_package(@current_resource.package_name, @new_resource.version, timeout)
    @new_resource.updated_by_last_action(true)
  else
  end
end

def removing_package?
  if @current_resource.version.nil?
    false # nothing to remove
  elsif @new_resource.version.nil?
    true # remove any version of a package
  elsif @new_resource.version == @current_resource.version
    true # remove the version we have
  else
    false # we don't have the version we want to remove
  end
end

def expand_options(options)
  options ? " #{options}" : ""
end

# these methods are the required overrides of 
# a provider that extends from Chef::Provider::Package 
# so refactoring into core Chef should be easy

def load_current_resource
  @current_resource = Chef::Resource::PythonPip.new(@new_resource.name)
  @current_resource.package_name(@new_resource.package_name)
  @current_resource.version(nil)
  
  unless current_installed_version.nil?
    @current_resource.version(current_installed_version)
  end
  
  @current_resource
end

def current_installed_version
  @current_installed_version ||= begin
    delimeter = /==/
    
    version_check_cmd = "pip freeze#{expand_virtualenv(can_haz_virtualenv(@new_resource))} | grep -i #{@new_resource.package_name}=="
    # incase you upgrade pip with pip!
    if @new_resource.package_name.eql?('pip')
      delimeter = /\s/
      version_check_cmd = "pip --version"
    end
    p = shell_out!(version_check_cmd)
    p.stdout.split(delimeter)[1].strip
  rescue Chef::Exceptions::ShellCommandFailed, Mixlib::ShellOut::ShellCommandFailed
  end
end

def candidate_version
  @candidate_version ||= begin
    # `pip search` doesn't return versions yet
    # `pip list` may be coming soon: 
    # https://bitbucket.org/ianb/pip/issue/197/option-to-show-what-version-would-be
    @new_resource.version||'latest'
  end
end

def install_package(name, version, timeout)
  v = "==#{version}" unless version.eql?('latest')
  shell_out!("pip install#{expand_options(@new_resource.options)}#{expand_virtualenv(can_haz_virtualenv(@new_resource))} #{name}#{v}", :timeout => timeout)
end

def upgrade_package(name, version, timeout)
  v = "==#{version}" unless version.eql?('latest')
  shell_out!("pip install --upgrade#{expand_options(@new_resource.options)}#{expand_virtualenv(can_haz_virtualenv(@new_resource))} #{@new_resource.name}#{v}", :timeout => timeout)
end

def remove_package(name, version, timeout)
  shell_out!("pip uninstall -y#{expand_options(@new_resource.options)}#{expand_virtualenv(can_haz_virtualenv(@new_resource))} #{@new_resource.name}", :timeout => timeout)
end

def expand_virtualenv(virtualenv)
  virtualenv && " --environment=#{virtualenv}"
end

# TODO remove when provider is moved into Chef core
# this allows PythonPip to work with Chef::Resource::Package
def can_haz_virtualenv(nr)
  nr.respond_to?("virtualenv") ? nr.virtualenv : nil
end
