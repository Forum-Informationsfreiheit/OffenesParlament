#!/bin/bash -l

#BASE
sudo apt-get update
sudo apt-get install -y python python-pip python-twisted vim

# requirements for scrapy
sudo apt-get update
sudo apt-get install -y python-dev libxml2-dev libxslt-dev libffi-dev

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
