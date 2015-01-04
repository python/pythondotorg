# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box      = 'ubuntu/trusty32'
  config.vm.hostname = 'pythondotorg'

  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.synced_folder ".", "/home/vagrant/pythondotorg"
  config.vm.provision :shell, path: 'Vagrant.sh', privileged: false, keep_color: true
end
