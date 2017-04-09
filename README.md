# OffenesParlament

An open-data framework for the public data of the Austrian Parliament

Check out the more complete documentation over at [offenesparlament.readthedocs.org](http://offenesparlament.readthedocs.org/en/latest/).

## Installation instructions with Vagrant

### Prerequisites

- [Vagrant](https://docs.vagrantup.com/v2/installation/index.html)
- [Vagrant Hostmanager Plugin](https://github.com/smdahlen/vagrant-hostmanager)
- [Virtualbox](https://www.virtualbox.org/)
- [Ansible](http://docs.ansible.com/ansible/intro_installation.html#installing-the-control-machine) (preferrably via `pip install ansible`)


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

### Provisioning

Vagrant provisioners can be used to update the dev setup and to flush the database:

'bootstrap' installs the necessary dependencies:

 ```
 vagrant provision --provision-with bootstrap
 ```

'reset_db' clears and re-creates the postgres database and runs migrations:

 ```
 vagrant provision --provision-with reset_db
 ```

## Documentation

Documentation is available via Sphinx. To generate cd to the `docs` directory and run:

```
make html
```

The documentation will then be available at ``docs/build/html/index.html``.

There is also an online version available over at [offenesparlament.readthedocs.org](http://offenesparlament.readthedocs.org/en/latest/).

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

There are currently five available scrapers, which should initially run in this order:

1. llp (legislative periods)
2. persons (for instance [Rudolf Anschober](http://www.parlament.gv.at/WWER/PAD_00024/index.shtml))
3. administrations (also persons, but those that are/were in a a Regierung)
4. pre_laws (for instance [Buchhaltungsagenturgesetz, Änderung (513/ME)](http://www.parlament.gv.at/PAKT/VHG/XXIV/ME/ME_00513/index.shtml))
5. laws_initiatives (for instance [ÖBIB-Gesetz 2015 (458 d.B.)](http://www.parlament.gv.at/PAKT/VHG/XXV/I/I_00458/index.shtml))

To run a scraper, use the following command:

```
python manage.py scrape crawl <scraper_name>
```

for instance:

```
python manage.py scrape crawl persons
```

The law_initiatives scraper also has an additional parameter to define, which legislative period to scan; per default, it scrapes the periods from XX to XV. This can be overriden this way:

```
python manage.py scrape crawl -a llp=21 laws_initiatives
```

to only scrape that period. Careful though: scraping of periods before the 20th legislative period is not possible as of yet (since there are no machine-readable documents available).

Furthermore, all of the scrapers try to utilize the parlament website's timestamp to skip objects that haven't changed since the were last scraped. To suppress this behaviour for a complete upgrade, add a `ignore_timestamp` parameter like so:

```
python manage.py scrape crawl -a ignore_timestamp=True laws_initiatives
```

## ElasticSearch and Re-Indexing

For now, reindexing (or updating the index, for that matter), is only done manually. To have all data indexed, just run:

```
python manage.py rebuild_index
```

for a full rebuild (wipes the indices first), or::

```
python manage.py update_index
```

to perform a simple update. For this to succeed, make sure ElasticSearch is up and running.

## Testing and Fixtures

The current repo contains a set of fixtures, which can be refreshed from the database by running:

```
python manage.py generate_fixtures
```

This creates the necessary fixtures to run the subscription tests in `op_scraper.tests.test_subscriptions`. 

A necessary precondition for running these tests might be to set postgresql's default collate and locale for new dbs. You can do so by entering a psql shell:

```
sudo -u postgres psql
```
and running the following commands:

```
UPDATE pg_database SET datistemplate=FALSE WHERE datname='template1';
DROP DATABASE template1;
CREATE DATABASE template1 WITH owner=postgres template=template0 encoding='UTF8' LC_CTYPE 'en_US.UTF-8' LC_COLLATE 'en_US.UTF-8';
UPDATE pg_database SET datistemplate=TRUE WHERE datname='template1';
```

This will redefine django's default settings for (test)databases it creates on the fly, otherwise there will be unicode import errors when django tries to import the fixtures:

```
Creating test database for alias 'default'...
Got an error creating the test database: encoding UTF8 does not match locale en_US
DETAIL:  The chosen LC_CTYPE setting requires encoding LATIN1.
```

## Staying in Contact

We have a mailing list now, sign up here:

https://lists.metalab.at/mailman/listinfo/offenesparlament_at


## License

you may find the license for the source code - excepting only some icons - 
in the `LICENSE` file
