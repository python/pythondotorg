gem_package "pg" do
  action :install
end

postgresql_connection_info = {
  :host     => 'localhost',
  :port     => node['postgresql']['config']['port'],
  :username => 'postgres',
  :password => node['postgresql']['password']['postgres']
}
postgresql_database_user 'vagrant' do
  connection postgresql_connection_info
  password   'pydotorg'
  action     :create
end

postgresql_database 'python.org' do
  connection postgresql_connection_info
  collation 'en_US.UTF-8'
  encoding 'UTF8'
  owner 'vagrant'
  action :create
end

execute "make_vagrant_superuser" do
  user "postgres"
  command "psql -U postgres -c 'ALTER USER vagrant CREATEUSER CREATEDB'"
end
