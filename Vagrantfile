Vagrant.configure("2") do |config|
  config.vm.box = "hashicorp/precise32"
  config.vm.synced_folder "offenesparlament", "/home/vagrant/offenesparlament"

  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.ignore_private_ip = false
  config.hostmanager.include_offline = true

  config.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 2

    # improve network connectivity
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
  end

  config.vm.define 'offenesparlament' do |node|
    node.vm.hostname = 'offenesparlament.vm'
    node.vm.network :private_network, ip: '192.168.47.15'
    node.vm.provision :shell, path: "bootstrap.sh"
  end
end
