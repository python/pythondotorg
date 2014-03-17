#
# Copyright 2012, Opscode, Inc.
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

require File.expand_path('../support/helpers', __FILE__)

describe 'postgresql::server' do
  include Helpers::Postgresql

  it 'installs the postgresql server packages' do
    node['postgresql']['server']['packages'].each do |pkg|
      package(pkg).must_be_installed
    end
  end

  it 'runs the postgresql service' do
    service((node['postgresql']['server']['service_name'] || 'postgresql')).must_be_running
  end

  it 'can connect to postgresql' do
    require 'pg'
    conn = PG::Connection.new(
                               :host => 'localhost',
                               :port => '5432',
                               :password => node['postgresql']['password']['postgres'],
                               :user => "postgres"
                             )
    assert_match(/localhost/, conn.host)
  end

end
