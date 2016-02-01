cd /vagrant/offenesparlament

python manage.py scrape crawl llp
python manage.py scrape crawl persons
python manage.py scrape crawl administrations
python manage.py scrape crawl pre_laws
python manage.py scrape crawl laws_initiatives
python manage.py scrape crawl auditors
python manage.py scrape crawl comittees
python manage.py scrape crawl inquiries
python manage.py scrape crawl petitions
python manage.py scrape crawl statement
