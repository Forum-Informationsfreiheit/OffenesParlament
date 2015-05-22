#!/bin/bash -l

#BASE
sudo apt-get update
sudo apt-get install -y python python-pip python-twisted vim curl

# requirements for scrapy
sudo apt-get update
sudo apt-get install -y python-dev libxml2-dev libxslt-dev libffi-dev

# requirements for django extensions
sudo apt-get update
sudo apt-get install graphviz

# install node.js and NPM
# install PPA first to get recent package
curl -sL https://deb.nodesource.com/setup | sudo bash -
sudo apt-get update
sudo apt-get install -y nodejs build-essential

# install client project requirements and the grunt-CLI task runner globally
cd /vagrant
npm install
sudo npm install -g grunt-cli

#django project requirements
cd /vagrant
sudo pip install -r requirements.txt

#set up django project with migrations and admin account
cd offenesparlament
python manage.py makemigrations
python manage.py migrate

# python manage.py createsuperuser
# Create the superuser without interaction. username: admin; password: admin
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | ./manage.py shell
