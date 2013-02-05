execute 'set_timezone' do
  command 'echo "America/New_York" | sudo tee /etc/timezone; sudo dpkg-reconfigure --frontend noninteractive tzdata'
end

user = "vagrant"

user "#{user}" do
  comment "#{user}"
  home "/home/#{user}"
  shell "/bin/bash"
  action :create
  supports  :manage_home => true
end


deploy_location = "/home/#{user}"

execute "echo 'source #{deploy_location}/ENV/bin/activate' >> #{deploy_location}/.bash_profile" do
  not_if "grep ENV/bin/activate #{deploy_location}/.bash_profile"
end

execute "echo 'alias remount=\"sudo mount -t vboxsf -o remount,uid=1000,gid=1000 pythondotorg /home/vagrant/pythondotorg\"' >> #{deploy_location}/.bash_profile" do
  not_if "grep remount #{deploy_location}/.bash_profile"
end

template "/bin/pyvenvex" do
  source "pyvenvex.py.erb"
  owner "#{user}"
  group "#{user}"
  mode 0755
  variables(
    :python3_path => "/usr/local/bin/python3.3"
  )
end

execute "pyvenv" do
  cwd "#{deploy_location}"
  user "#{user}"
  group "#{user}"
  command "pyvenvex --clear ENV"
  not_if { ::File.exists?("/ENV/bin/activate") }
end

ve_path = "#{deploy_location}/ENV"

manage_py = "cd #{deploy_location}/pythondotorg/; #{::File.join(ve_path, "bin", "python")} manage.py"


execute "#{::File.join(ve_path, "bin", "pip")} install -r /home/vagrant/pythondotorg/requirements.txt" do
  user "#{user}"
end

execute "#{manage_py} syncdb --noinput" do
  user "#{user}"
  cwd "#{deploy_location}/pythondotorg/"
end

# Can't have migrations until South is in Python 3...
# execute "#{manage_py} migrate" do
#   user "#{user}"
#   cwd "#{deploy_location}/pythondotorg/"
# end
