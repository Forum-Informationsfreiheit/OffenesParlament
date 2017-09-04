#!/bin/bash -l

#BASE
# for postgres
sudo locale-gen de_DE.UTF-8
sudo apt-get -qq update
sudo apt-get install debian-archive-keyring
sudo apt-get install -y python python-pip python-twisted vim curl python-software-properties git htop postgresql libpq-dev

# requirements for scrapy
sudo apt-get -qq update
sudo apt-get install -y python-dev libxml2-dev libxslt-dev libffi-dev libssl-dev

# requirements for django extensions
sudo apt-get -qq update
sudo apt-get install -y graphviz

# requirements for celery
sudo apt-get -qq update
sudo apt-get install -y rabbitmq-server
sudo rabbitmqctl add_user offenesparlament op_dev_qwerty
sudo rabbitmqctl add_vhost offenesparlament.vm
sudo rabbitmqctl set_permissions -p offenesparlament.vm offenesparlament ".*" ".*" ".*"
sudo rabbitmqctl set_permissions -p / offenesparlament ".*" ".*" ".*"

# elasticsearch & requirements
# open JDK 7
# kopf plugin for elastic search
wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
add-apt-repository -r "deb http://packages.elastic.co/elasticsearch/1.6/debian stable main"
echo "deb http://packages.elastic.co/elasticsearch/1.6/debian stable main" | sudo tee -a /etc/apt/sources.list
sudo apt-get -qq update
sudo apt-get -y install openjdk-7-jre elasticsearch
sudo sed -i 's/\/var\/run\/elasticsearch/\/var\/run/g' /etc/init.d/elasticsearch
sudo update-rc.d elasticsearch defaults 95 10
sudo /usr/share/elasticsearch/bin/plugin --install lmenezes/elasticsearch-kopf
sudo /etc/init.d/elasticsearch restart

# supervisor
sudo pip install pip --upgrade
sudo pip install supervisor psycopg2 requests[security]
sudo pip install ndg-httpsclient --upgrade
sudo cp /vagrant/provision/conf/supervisord.conf /etc/
mkdir -p /vagrant/ignore/var/log
sudo supervisord

# Install specific version of ansible that works with vagrant 1.8.1
sudo pip install ansible==1.9.4

# Upgrade pyasn1 version so scraping works again
sudo pip install pyasn1==0.1.9

# install node.js and NPM
# install PPA first to get recent package
#curl -sL https://deb.nodesource.com/setup | sudo bash -
curl -sL https://deb.nodesource.com/setup_4.x | sudo bash -
sudo apt-get -qq update
sudo apt-get install -y nodejs build-essential

# install client project requirements and the grunt-CLI task runner globally
cd /vagrant
npm install
sudo npm install -g grunt-cli

# install sass
sudo gem install sass

# re-install setuptools. Something removed them during provisioning
wget https://bootstrap.pypa.io/get-pip.py -O - | sudo python

#django project requirements
cd /vagrant
sudo pip install -r requirements.txt
sudo pip install -r requirements.dev.txt

#django-configuration: set Dev environment variable on login
echo 'DJANGO_CONFIGURATION="Dev"; export DJANGO_CONFIGURATION' >> ~/.profile
