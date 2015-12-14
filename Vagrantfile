Vagrant.configure("2") do |config|
  config.vm.box = "hashicorp/precise32"
  config.vm.synced_folder "offenesparlament", "/home/vagrant/offenesparlament"

  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.ignore_private_ip = false
  config.hostmanager.include_offline = true

  # python manage.py runserver 0.0.0.0:8000 default port
  config.vm.network :forwarded_port, host: 8000, guest: 8000
  # celery flower management interface default port
  config.vm.network :forwarded_port, host: 5555, guest: 5555
  # elasticsearch default port
  config.vm.network :forwarded_port, host: 9200, guest: 9200

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


    ##
    # Provisioners
    ##

    # 1. Bootstrap provisioner, installs the dev system and dependencies
    config.vm.provision "bootstrap", type: "shell", path: "provision/bootstrap.sh", privileged: false

    # 2. DB Creation and Reset provisioner
    node.vm.provision "reset_db", type: "ansible", playbook: "provision/reset_postgresdb.yml"
    #, verbose: "vvv"

  end
end
