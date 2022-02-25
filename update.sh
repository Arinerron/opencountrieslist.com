#!/bin/sh

sudo su -c 'cd /var/www/countryscrape && git pull && python3 ./main.py && chown -R root:www-data /var/www/countryscrape'
