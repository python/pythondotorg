# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.network "forwarded_port", guest: 8000, host: 8001
  config.vm.synced_folder ".", "/home/vagrant/pythondotorg"
  config.vm.network "public_network"
  config.vm.provider "virtualbox" do |v|
    v.memory = 2048
  end
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "provisioning/pythondotorg.yml"
    ansible.host_key_checking = false
  end
  config.ssh.forward_agent = true
end
