#
# Cookbook Name:: ruby
# Definition:: ruby_packages
#
# Copyright 2008-2009, Opscode, Inc.
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

define :ruby_packages, :action => :install do
  rv = params[:name].to_s
  raise "A Ruby version such as 1.8, 1.9 or 1.9.1 must be given" if rv.empty?

  packages = case node[:platform]
  when "ubuntu","debian"
    [
      "ruby#{rv}",
      "ruby#{rv}-dev",
      "rdoc#{rv}",
      "ri#{rv}",
      "irb#{rv}",
      "libopenssl-ruby#{rv}",
     ("libshadow-ruby1.8" if rv == "1.8")
    ].compact

  when "gentoo"
    rv = rv.slice(0..2)
    target = "ruby" + rv.delete('.')

    [
      # ruby-ssl is before ruby to ensure that ruby is initially
      # installed with the ssl USE flag enabled.
      "virtual/ruby-ssl:#{target}",
      "dev-lang/ruby:#{rv}",
      "virtual/ruby-rdoc:#{target}",
     ("dev-ruby/ruby-shadow" if rv == "1.8")
    ].compact

  when "centos","redhat","fedora"
    # yum requires full version numbers. :(
    %w{
      ruby
      ruby-libs
      ruby-devel
      ruby-docs
      ruby-ri
      ruby-irb
      ruby-rdoc
      ruby-mode
    }

  when "arch"
    # 1.8 only available from AUR. :(
    %w{
      ruby
      ruby-docs
    }
  end

  unless packages.nil?
    packages.each do |pkg|
      package pkg do
        action params[:action]
      end
    end
  end
end
