::Chef::Recipe.send(:include, Opscode::OpenSSL::Password)

execute 'set_timezone' do
  command 'echo "America/New_York" | sudo tee /etc/timezone; sudo dpkg-reconfigure --frontend noninteractive tzdata'
end


template "#{node[:postgresql][:dir]}/pg_hba.conf" do
  source "pg_hba.conf.erb"
  owner "postgres"
  group "postgres"
  mode 0600
  notifies :reload, resources(:service => "postgresql"), :immediately
end

# create database
username = node["pythondotorg"]["database"]["user"]

postgresql_connection_info = {:host => node["pythondotorg"]["database"]["host"], :port => node["pythondotorg"]["database"]["port"], :username => "postgres", :password => node['postgresql']['password']['postgres']}

node.set_unless['pythondotorg']['database']['password'] = secure_password

postgresql_database_user username do
  connection postgresql_connection_info
  password node["pythondotorg"]["database"]["password"]
  action :create
end

# Clear connections to the template before creating a new DB.
execute "clear_postgres_connections" do
  command 'psql -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.procpid) 
                                  FROM pg_stat_activity 
                                  WHERE pg_stat_activity.datname = \'template1\';"'
end

postgresql_database node["pythondotorg"]["database"]["name"] do
  connection postgresql_connection_info
  owner username
  action :create
end

postgresql_database_user username do
  connection postgresql_connection_info
  database_name node["pythondotorg"]["database"]["name"]
  action :grant
end

execute "make_superuser" do
    code = <<-EOH
    psql -U postgres -c "select * from pg_user where usesuper='t'" | grep -c #{username}
    EOH
    command "psql -U postgres -c 'ALTER USER #{username} CREATEUSER CREATEDB'"
    not_if code 
end
