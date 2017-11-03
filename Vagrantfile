# vi: set ft=ruby :

Vagrant.require_version ">= 1.7.0"

Vagrant.configure(2) do |config|
  # TODO: https://askubuntu.com/a/854396
  config.vm.box = "bento/ubuntu-16.04"
  config.vm.boot_timeout = 1200
  config.vm.network "forwarded_port", guest: 8000, host: 8001
  config.vm.synced_folder ".", "/home/vagrant/pythondotorg"
  config.vm.provider "virtualbox" do |v|
    v.memory = 2048
  end
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "provisioning/pythondotorg.yml"
    ansible.host_key_checking = false
  end
  config.ssh.insert_key = false
  config.ssh.forward_agent = true
end
