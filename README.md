# OffenesParlament

An open-data framework for the public data of the Austrian Parliament

## Quick-And-Dirty installation instructions

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
6. Try it out!
 
 ```
 python manage.py runserver
 ```

And you're done!

## Proof-Of-Concept Scrapy spider

The sample scraper for the laws and initiatives pages (for instance, [ÖBIB-Gesetz 2015 (458 d.B.)](http://www.parlament.gv.at/PAKT/VHG/XXV/I/I_00458/index.shtml)) of the Austrian Parliament can be run by doing this:

```
cd scripts
python parse_laws.py
```

The script will not terminate by itself after it has output the information it found, so you will have to terminate it manually with CTRL+c.
