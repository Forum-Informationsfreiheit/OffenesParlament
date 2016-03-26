cd /vagrant/offenesparlament

python manage.py scrape crawl llp
python manage.py scrape crawl persons
python manage.py scrape crawl administrations
python manage.py scrape crawl pre_laws -a llp=25
python manage.py scrape crawl laws_initiatives -a llp=25
python manage.py scrape crawl auditors
python manage.py scrape crawl comittees -a llp=25
python manage.py scrape crawl inquiries -a llp=25
python manage.py scrape crawl petitions -a llp=25
python manage.py scrape crawl statement -a llp=25

# run es rebuild
python manage.py rebuild_index --noinput
