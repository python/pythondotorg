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

execute "echo 'alias remount=\"sudo mount -t vboxsf -o remount,uid=1000,gid=1000 pythondotorg /home/vagrant/pythondotorg\"' >> #{deploy_location}/.bash_profile" do
  not_if "grep remount #{deploy_location}/.bash_profile"
end

python_virtualenv "/home/vagrant/ENV" do
  interpreter "python3.3"
  owner "vagrant"
  group "vagrant"
  action :create
end

ve_path = "#{deploy_location}/ENV"

manage_py = "cd #{deploy_location}/pythondotorg/; #{::File.join(ve_path, "bin", "python")} manage.py"


python_pip "-r /home/vagrant/pythondotorg/requirements.txt" do
  virtualenv "/home/vagrant/ENV"
  user "vagrant"
end

execute "#{manage_py} syncdb --noinput" do
  user "#{user}"
  cwd "#{deploy_location}/pythondotorg/"
end

execute "#{manage_py} migrate" do
  user "#{user}"
  cwd "#{deploy_location}/pythondotorg/"
end

execute "echo 'source #{deploy_location}/ENV/bin/activate' >> #{deploy_location}/.bash_profile" do
  not_if "grep ENV/bin/activate #{deploy_location}/.bash_profile"
end
