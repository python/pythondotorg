if not %w(etch lenny lucid precise sid squeeze wheezy).include? node['postgresql']['pgdg']['release_apt_codename']
  raise "Not supported release by PGDG apt repository"
end

include_recipe 'apt'

file "remove deprecated Pitti PPA apt repository" do
  action :delete
  path "/etc/apt/sources.list.d/pitti-postgresql-ppa"
end

apt_repository 'apt.postgresql.org' do
  uri 'http://apt.postgresql.org/pub/repos/apt'
  distribution "#{node['postgresql']['pgdg']['release_apt_codename']}-pgdg"
  components ['main', node['postgresql']['version']]
  key 'http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc'
  action :add
end
