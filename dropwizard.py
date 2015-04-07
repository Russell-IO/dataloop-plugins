#!/usr/bin/env python

import urllib2
import json
import datetime
import time
import socket
import re
import sys, getopt
import os

# FUNCTIONS #

def create_msg(dict, timestamp):
    message = ""
    for k,v in dict.items():
        message += "%s %s %s\n" % (k, v, timestamp)
    return message


# send metrics to graphite
def send_msg(message, graphite_host, graphite_port):
    # print "Sending message:\n%s" % message
    try:
        sock = socket.socket()
    except socket.error, msg:
        print 'CRITICAL - Failed to create socket. Error code: %s - %s' % (msg[0], msg[1])
        sys.exit(2)
    try:
        sock.connect((graphite_host, int(graphite_port)))
    except Exception, e:
        print('CRITICAL - something is wrong with %s:%s. Exception is %s' % (graphite_host, graphite_port, e))
        sys.exit(2)
    sock.sendall(message)
    sock.close



def flatten(structure, key="", path="", flattened=None):
    if flattened is None:
        flattened = {}

    if type(structure) not in (dict, list):
        flattened[((path + ".") if path else "") + key] = structure
    elif isinstance(structure, list):
        for i, item in enumerate(structure):
            flatten(item, "%d" % i, path + "." + key, flattened)
    else:
        for new_key, value in structure.items():
            flatten(value, new_key, path + "." + key, flattened)
    return flattened


# ensure no spaces in any keys
def replace_spaces(dict):
    for k in dict.keys():
        if re.match('(\S+\s\S+)', k):
            nk = k.replace(' ', '_')
            dict[nk] = dict[k]
            dict.pop(k)
    return dict


def strip_unicode(dict):
    for k,v in dict.items():
        if type(v) == unicode:
            dict.pop(k)
    return dict


def fetch_metrics(url):
    try:
        r = urllib2.urlopen(url)
        data = json.load(r)
    except:
        print "CRITICAL - Unable to fetch metrics from: %s" % url
        sys.exit(2)
    return data


def main(argv):

    #### Settings ####

    CARBON_SERVER   = ''
    CARBON_PORT     = 2003
    DROPWIZARD_HOST = 'localhost'
    DROPWIZARD_PORT = ''
    DROPWIZARD_PATH = '/metrics'
    SERVICE         = ''
    THIS_SERVER     = os.uname()[1]
    NOW             = datetime.datetime.now()
    UNIX_TIME       = int(time.mktime(NOW.timetuple()))


    help = "%s -H <hostname> -p <port> -u <urlpath> -s <servicename>" \
            " -G <graphiteserver> [-g <graphiteport>]" % sys.argv[0]

    try:
        opts, args = getopt.getopt(argv, "hH:p:u:s:G:g:", ["hostname=", "port=",
                                         "urlpath=", "servicename=",
                                         "graphitehost=", "graphiteport="])
    except:
        print help
        sys.exit(2)

    if len(opts) < 1:
        print "No args specified:\n%s" % help
        sys.exit(1)

    for opt, arg in opts:
        if opt == '-h':
            print "Help:\n%s" %help
            sys.exit()
        elif opt in ('-H', '--hostname'):
            DROPWIZARD_HOST = arg
        elif opt in ('-p', '--port'):
            DROPWIZARD_PORT = arg
        elif opt in ('-u', '--urlpath'):
            DROPWIZARD_PATH = arg
        elif opt in ('-s', '--servicename'):
            SERVICE = arg
        elif opt in ('-G', '--graphitehost'):
            CARBON_SERVER = arg
        elif opt in ('-g', '--graphiteport'):
            CARBON_PORT = int(arg)
        else:
            print "Invalid argument passed:\n%s" % help

    if len(SERVICE) == 0:
        print "servicename cannot be blank\n\n%s" % help
        sys.exit(2)
    if len(CARBON_SERVER) == 0:
        print "graphitehost cannot be blank\n\n%s" % help


    url = "http://%s:%s%s" % (DROPWIZARD_HOST, DROPWIZARD_PORT, DROPWIZARD_PATH)
    json_metrics = fetch_metrics(url)

    fm = flatten(json_metrics, path="%s" % (SERVICE), key=THIS_SERVER)

    # strip non-numerics and replace any space
    fm = strip_unicode(fm)
    fm = replace_spaces(fm)

    # generate something plausible for graphite and fire!
    message = create_msg(fm, UNIX_TIME)
    send_msg(message, CARBON_SERVER, CARBON_PORT)


    print "OK - metrics sent"


if __name__ == "__main__":
    main(sys.argv[1:])


