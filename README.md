# OffenesParlament

An open-data framework for the public data of the Austrian Parliament

## Installation instructions with Vagrant

### Prerequisites

- [Vagrant](https://docs.vagrantup.com/v2/installation/index.html)
- [Vagrant Hostmanager Plugin](https://github.com/smdahlen/vagrant-hostmanager)
- [Virtualbox](https://www.virtualbox.org/)


### Setup

1. Clone the github repository (duh)
2. Navigate into the project dir `cd OffenesParlament`
3. Setup and run the vagrant VM `vagrant up`. All requirements will be
   installed automatically inside the VM which may take a few minutes
   the first time.
4. The script might ask you for your password as it will add
   offenesparlament.vm pointing to this VM to your hosts-file. It also
   automatically creates a django superuser `admin` with password `admin`.
5. Log in to the running VM with `vagrant ssh`
6. For the initial scraping instructions see below
7. Run the server inside the VM (0.0.0.0 lets the server respond to
   requests from outside the VM - ie your physical machine where you
   probably run your browser)

 ```
 cd offenesparlament
 python manage.py runserver 0.0.0.0:8000
 ```

8. If you work on client files that have to be compiled (CSS, JS) you
   have to run grunt as well. ATM we have the tasks `dev` and `reloading`.
   `dev` watches and regenerates files when their sources change.
   (Remember that sources also change when you do a git pull and
   generated client files aren't commited to git) And `reloading` does
   that and uses [Browsersync](http://www.browsersync.io/) to reload your browser when files
   change.

 ```
 cd /vagrant
 grunt dev
 ```

9. To exit and shutdown the VM run

 ```
 exit
 vagrant halt
 ```



## Quick-And-Dirty installation instructions (on your own machine)

Follow these instructions (updates pending!) to set up the project as is.

1. Clone the github repository (duh)
2. Install python [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) and [virtualenvwrapper](https://virtualenvwrapper.readthedocs.org/en/latest/) (if you don't have it yet):

 ```
 pip install virtualenv
 pip install virtualenvwrapper
 ```
 Depending on your operating system, you might have to do some additional setup as explained [here](https://virtualenvwrapper.readthedocs.org/en/latest/#introduction).
3. Create a new python virtualenv for your project:

 ```
 mkvirtualenv openparliament
 ```
 If all went well, your shell should have activated the environment already.
4. Install the projects dependencies:

 ```
 pip install -r requirements.txt
 ```
5. Have django create the DB-models:

 ```
 cd offenesparlament
 python manage.py makemigrations
 python manage.py migrate
 ```

6. Create a superuser to log in to the backend with

 ```
 python manage.py createsuperuser
 ```

7. Try it out!

 ```
 python manage.py runserver
 ```

  Navigate to the [Django Admin Tool](http://127.0.0.1:8000/admin/) and check out your sweet, sweet models!

And you're done!

## Resetting the database

In case you need to reset the database (delete all migrations, flush the db content, recreate all objects etc.), run these commands in the django project folder 'offenesparlament':

```
bin/clear_db.sh
```

## Creating a Model-Diagram

It's possible to view the current database model residing in the op_scraper app by calling:

```
bin/graph_models.sh
```

A png-image will be generated as ``ignore/models.png``.

## Initial scraping

There are currently four available scrapers, which should initially run in this order:

1. llp (legislative periods)
2. persons (for instance [Rudolf Anschober](http://www.parlament.gv.at/WWER/PAD_00024/index.shtml))
3. pre_laws (for instance [Buchhaltungsagenturgesetz, Änderung (513/ME)](http://www.parlament.gv.at/PAKT/VHG/XXIV/ME/ME_00513/index.shtml))
4. laws_initiatives (for instance [ÖBIB-Gesetz 2015 (458 d.B.)](http://www.parlament.gv.at/PAKT/VHG/XXV/I/I_00458/index.shtml))

To run a scraper, use the following command:

```
python manage.py scrape crawl <scraper_name>
```

for instance:

```
python manage.py scrape crawl persons
```

