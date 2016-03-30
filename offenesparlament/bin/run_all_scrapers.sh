#!/bin/bash

FOLDER="/vagrant/offenesparlament"
if [ "$#" -gt 0 ]; then
  FOLDER=$1
fi

CMD="python manage.py"
if [ "$#" -gt 1 ]; then
  CMD=$2
fi


cd $FOLDER

eval "$CMD scrape crawl llp"
eval "$CMD scrape crawl persons"
eval "$CMD scrape crawl administrations"
eval "$CMD scrape crawl pre_laws"
eval "$CMD scrape crawl laws_initiatives"
eval "$CMD scrape crawl auditors"
eval "$CMD scrape crawl comittees"
eval "$CMD scrape crawl inquiries"
eval "$CMD scrape crawl petitions"
eval "$CMD scrape crawl statement"

# run es rebuild
eval "$CMD rebuild_index --noinput"
