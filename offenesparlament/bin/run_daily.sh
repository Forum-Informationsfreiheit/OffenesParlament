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
eval "$CMD scrape crawl auditors"
eval "$CMD scrape crawl pre_laws -a llp=25"
eval "$CMD scrape crawl laws_initiatives -a llp=25"
eval "$CMD scrape crawl comittees -a llp=25"
eval "$CMD scrape crawl inquiries -a llp=25"
eval "$CMD scrape crawl petitions -a llp=25"
eval "$CMD scrape crawl statement -a llp=25"

# run es update
eval "$CMD update_index op_scraper.Debate -b 100"
eval "$CMD update_index op_scraper.Law -b 1000"
eval "$CMD update_index op_scraper.Person"

eval "$CMD check_subscriptions"
