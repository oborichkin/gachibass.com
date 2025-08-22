#!/bin/sh

envsubst < radio.liq.template > radio.liq

/usr/bin/liquidsoap radio.liq