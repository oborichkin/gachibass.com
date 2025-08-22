#!/bin/sh

envsubst < icecast.xml.template > /etc/icecast2/icecast.xml

exec "$@"
