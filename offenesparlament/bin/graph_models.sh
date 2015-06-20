#!/bin/bash
mkdir -p ignore
python manage.py graph_models op_scraper |dot -Tpng -o ignore/models.png