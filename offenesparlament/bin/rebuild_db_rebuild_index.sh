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

eval "$CMD scrape crawl llp -a ignore_timestamp=1"
eval "$CMD scrape crawl persons -a ignore_timestamp=1"
eval "$CMD scrape crawl administrations -a ignore_timestamp=1"
eval "$CMD scrape crawl pre_laws -a ignore_timestamp=1"
eval "$CMD scrape crawl laws_initiatives -a ignore_timestamp=1"
eval "$CMD scrape crawl auditors -a ignore_timestamp=1"
eval "$CMD scrape crawl comittees -a ignore_timestamp=1"
eval "$CMD scrape crawl inquiries -a ignore_timestamp=1"
eval "$CMD scrape crawl petitions -a ignore_timestamp=1"
eval "$CMD scrape crawl statement -a ignore_timestamp=1"

# run es update
eval "$CMD update_index op_scraper.Debate -b 25"
eval "$CMD update_index op_scraper.Law -b 500"
eval "$CMD update_index op_scraper.Person -b 100"

eval "$CMD reset_all_content_hashes"
