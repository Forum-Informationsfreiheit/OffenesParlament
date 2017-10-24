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

eval "$CMD scrape crawl llp -L INFO"
eval "$CMD scrape crawl persons -L INFO"
eval "$CMD scrape crawl administrations -L INFO"
eval "$CMD scrape crawl pre_laws -a llp=25 -L INFO"
eval "$CMD scrape crawl laws_initiatives -a llp=25 -L INFO"
eval "$CMD scrape crawl auditors -L INFO"
eval "$CMD scrape crawl comittees -a llp=25 -L INFO"
eval "$CMD scrape crawl inquiries -a llp=25 -L INFO"
eval "$CMD scrape crawl petitions -a llp=25 -L INFO"
eval "$CMD scrape crawl statement -a llp=25 -L INFO"

# run es rebuild
eval "$CMD rebuild_index --noinput"
