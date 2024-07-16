#!/bin/bash

username="$1"
password="$2"
salt=$(uuidgen | tr '[:upper:]' '[:lower:]')
hash=$(echo -n $password | argon2 $salt -i -t 3 -p 1 -m 12 -e)
echo "$username:$hash"
