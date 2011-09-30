#!/bin/bash
# Sparker5 spawn-fcgi
# Used to start or stop FastCGI process
# 
# Written by Sparker5 team
# Http://sparker5.com
# 
# License: MIT
# Http://www.opensource.org/licenses/mit-license.php

#==============================
# reset your own config before run
PWD="your webpy path"           #like: /opt/my-site
APPNAME="your webpy app name"   #like: app.py
SERVERPORT="55555"
PROCESSAMOUNT="8"
PIDFILE="/var/run/your-project-name.pid"
# =============================


if [ "x$(whoami)" != "xroot" ]; then
    echo "Only root can run this script."
    exit 1
fi

case $1 in
    "start")
        export PYTHON_EGG_CACHE="/tmp/.python-eggs"
        cp "${PIDFILE}" "${PIDFILE}.bak" 2>/dev/null
        spawn-fcgi -f "${PWD}/${APPNAME}" -d "${PWD}" -a 127.0.0.1 -p ${SERVERPORT} \
            -F ${PROCESSAMOUNT} -P "${PIDFILE}" -u www-data -g www-data
        ret=$?
        if [ "x${ret}" == "x0" ]; then
            echo "" >> "${PIDFILE}"
            rm "${PIDFILE}.bak" 2>/dev/null
        else
            mv "${PIDFILE}.bak" "${PIDFILE}" 2>/dev/null
        fi
        exit ${ret}
        ;;
    "stop")
        if [ -f "${PIDFILE}" ]; then
            while read pid; do
                if [[ -d "/proc/${pid}" && \
                    $(stat -c "%U %G" "/proc/${pid}") == \
                    "www-data www-data" ]]; then
                    grep "${APPNAME}" "/proc/${pid}/cmdline" 1>/dev/null 2>&1
                    if [ "x$?" == "x0" ]; then
                        kill -KILL ${pid}
                    fi
                fi
            done < "${PIDFILE}"
            rm "${PIDFILE}" 2>/dev/null
        fi
        ;;
    *)
        echo "usage: $(basename $0) {start|stop}"
        exit 1
        ;;
esac
