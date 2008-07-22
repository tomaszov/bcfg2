#! /usr/bin/env python
'''Imports statistics.xml and clients.xml files in to database backend for new statistics engine'''
__revision__ = '$Revision$'

import os, sys, binascii
try:
    import Bcfg2.Server.Reports.settings
except:
    sys.stderr.write("Failed to load configuration settings. is /etc/bcfg2.conf readable?")
    sys.exit(1)

project_directory = os.path.dirname(Bcfg2.Server.Reports.settings.__file__)
project_name = os.path.basename(project_directory)
sys.path.append(os.path.join(project_directory, '..'))
project_module = __import__(project_name, '', '', [''])
sys.path.pop()
# Set DJANGO_SETTINGS_MODULE appropriately.
os.environ['DJANGO_SETTINGS_MODULE'] = '%s.settings' % project_name

from Bcfg2.Server.Reports.reports.models import Client, Interaction, Bad, Modified, Extra, Performance, Reason, Ping
from lxml.etree import XML, XMLSyntaxError
from getopt import getopt, GetoptError
from datetime import datetime
from time import strptime
from django.db import connection
import ConfigParser

def build_reason_kwargs(r_ent):
    if r_ent.get('current_bdiff', False):
        rc_diff = binascii.a2b_base64(r_ent.get('current_bdiff'))
    else:
        rc_diff = r_ent.get('current_diff', '')
    return dict(owner=r_ent.get('owner', default=""),
                current_owner=r_ent.get('current_owner', default=""),
                group=r_ent.get('group', default=""),
                current_group=r_ent.get('current_group', default=""),
                perms=r_ent.get('perms', default=""),
                current_perms=r_ent.get('current_perms', default=""),
                status=r_ent.get('status', default=""),
                current_status=r_ent.get('current_status', default=""),
                to=r_ent.get('to', default=""),
                current_to=r_ent.get('current_to', default=""),
                version=r_ent.get('version', default=""),
                current_version=r_ent.get('current_version', default=""),
                current_exists=r_ent.get('current_exists', default="True").capitalize()=="True",
                current_diff=rc_diff)


def load_stats(cdata, sdata, vlevel):
    cursor = connection.cursor()
    clients = {}
    cursor.execute("SELECT name, id from reports_client;")
    [clients.__setitem__(a, b) for a, b in cursor.fetchall()]
    
    for node in sdata.findall('Node'):
        name = node.get('name')
        if not clients.has_key(name):
            cursor.execute(\
                "INSERT INTO reports_client VALUES (NULL, %s, %s, NULL, NULL)",
                [datetime.now(), name])
            clients[name] = cursor.lastrowid
            if vlevel > 0:
                print("Client %s added to db" % name)
        else:
            if vlevel > 0:
                print("Client %s already exists in db" % name)

    pingability = {}
    [pingability.__setitem__(n.get('name'), n.get('pingable', default='N')) \
     for n in cdata.findall('Client')]

    for node in sdata.findall('Node'):
        name = node.get('name')
        c_inst = Client.objects.filter(id=clients[name])[0]
        try:
            pingability[name]
        except KeyError:
            pingability[name] = 'N'
        for statistics in node.findall('Statistics'):
            t = strptime(statistics.get('time'))
            # Maybe replace with django.core.db typecasts typecast_timestamp()?
            # import from django.backends util
            timestamp = datetime(t[0], t[1], t[2], t[3], t[4], t[5])
            ilist = Interaction.objects.filter(client=c_inst,
                                               timestamp=timestamp)
            if ilist:
                current_interaction_id = ilist[0].id
                if vlevel > 0:
                    print("Interaction for %s at %s with id %s already exists"%(clients[name],
                        datetime(t[0],t[1],t[2],t[3],t[4],t[5]),current_interaction_id))
                continue
            else:
                newint = Interaction(client=c_inst,
                                     timestamp=timestamp,
                                     state=statistics.get('state', default="unknown"),
                                     repo_revision=statistics.get('revision',default="unknown"),
                                     client_version=statistics.get('client_version',default="unknown"),
                                     goodcount=statistics.get('good',default="0"),
                                     totalcount=statistics.get('total',default="0"))
                newint.save()
                current_interaction_id = newint.id
                if vlevel > 0:
                    print("Interaction for %s at %s with id %s INSERTED in to db"%(clients[name],
                        timestamp, current_interaction_id))


            pattern = [('Bad/*', Bad, 'reports_bad'),
                       ('Extra/*', Extra, 'reports_extra'),
                       ('Modified/*', Modified, 'reports_modified')]
            for (xpath, obj, tablename) in pattern:
                for x in statistics.findall(xpath):
                    kargs = build_reason_kwargs(x)
                    if '-O3' not in sys.argv:
                        rls = Reason.objects.filter(**kargs)
                    else:
                        rls = []

                    if rls:
                        rr = rls[0]
                        if vlevel > 0:
                            print "Reason exists: %s"% (rr.id)
                    else:
                        rr = Reason(**kargs)
                        rr.save()
                        if vlevel > 0:
                            print "Created reason: %s" % rr.id
                    if '-O3' not in sys.argv:
                        links = obj.objects.filter(name=x.get('name'),
                                                   kind=x.tag,
                                                   reason=rr)
                    else:
                        links = []
                        
                    if links:
                        item_id = links[0].id
                        if vlevel > 0:
                            print "%s item exists, has reason id %s and ID %s" % (xpath, rr.id, item_id)
                    else:
                        newitem = obj(name=x.get('name'),
                                      kind=x.tag, critical=False,
                                      reason=rr)
                        newitem.save()
                        item_id = newitem.id
                        if vlevel > 0:
                            print "%s item INSERTED having reason id %s and ID %s" % (xpath, rr.id, item_id)
                    try:
                        cursor.execute("INSERT INTO "+tablename+"_interactions VALUES (NULL, %s, %s);",
                                       [item_id, current_interaction_id])
                    except:
                        pass                    

            for times in statistics.findall('OpStamps'):
                for metric, value in times.items():
                    if '-O3' not in sys.argv:
                        mmatch = Performance.objects.filter(metric=metric, value=value)
                    else:
                        mmatch = []
                    
                    if mmatch:
                        item_id = mmatch[0].id
                    else:
                        mperf = Performance(metric=metric, value=value)
                        mperf.save()
                        item_id = mperf.id
                    try:
                        cursor.execute("INSERT INTO reports_performance_interaction VALUES (NULL, %s, %s);",
                                       [item_id, current_interaction_id])
                    except:
                        pass

    if vlevel > 1:
        print("----------------INTERACTIONS SYNCED----------------")
    cursor.execute("select reports_interaction.id, x.client_id from (select client_id, MAX(timestamp) as timer from reports_interaction Group BY client_id) x, reports_interaction where reports_interaction.client_id = x.client_id AND reports_interaction.timestamp = x.timer")
    for row in cursor.fetchall():
        cursor.execute("UPDATE reports_client SET current_interaction_id = %s where reports_client.id = %s",
                       [row[0],row[1]])
    if vlevel > 1:
        print("------------LATEST INTERACTION SET----------------")

    for key in pingability.keys():
        if key not in clients:
            #print "Ping Save Problem with client %s" % name
            continue
        cmatch = Client.objects.filter(id=clients[key])[0]
        pmatch = Ping.objects.filter(client=cmatch).order_by('-endtime')
        if pmatch:
            if pmatch[0].status == pingability[key]:
                pmatch[0].endtime = datetime.now()
                pmatch[0].save()
            else:
                newp = Ping(client=cmatch, status=pingability[key],
                            starttime=datetime.now(),
                            endtime=datetime.now())
                newp.save()
        else:
            newp = Ping(client=cmatch, status=pingability[key],
                        starttime=datetime.now(), endtime=datetime.now())
            newp.save()

    if vlevel > 1:
        print "---------------PINGDATA SYNCED---------------------"

    connection._commit()
    #Clients are consistent

if __name__ == '__main__':
    from sys import argv
    verb = 0
    cpath = "/etc/bcfg2.conf"
    clientpath = False
    statpath = False
    
    try:
        opts, args = getopt(argv[1:], "hvudc:s:", ["help", "verbose", "updates" ,
                                                   "debug", "clients=", "stats=",
                                                   "config="])
    except GetoptError, mesg:
        # print help information and exit:
        print "%s\nUsage:\nimportscript.py [-h] [-v] [-u] [-d] [-C bcfg2 config file] [-c clients-file] [-s statistics-file]" % (mesg) 
        raise SystemExit, 2

    for o, a in opts:
        if o in ("-h", "--help"):
            print "Usage:\nimportscript.py [-h] [-v] -c <clients-file> -s <statistics-file> \n"
            print "h : help; this message"
            print "v : verbose; print messages on record insertion/skip"
            print "u : updates; print status messages as items inserted semi-verbose"
            print "d : debug; print most SQL used to manipulate database"
            print "C : path to bcfg2.conf config file."
            print "c : clients.xml file"
            print "s : statistics.xml file"
            raise SystemExit
        if o in ["-C", "--config"]:
            cpath = a

        if o in ("-v", "--verbose"):
            verb = 1
        if o in ("-u", "--updates"):
            verb = 2
        if o in ("-d", "--debug"):
            verb = 3
        if o in ("-c", "--clients"):
            clientspath = a

        if o in ("-s", "--stats"):
            statpath = a

    cf = ConfigParser.ConfigParser()
    cf.read([cpath])

    if not statpath:
        try:
            statpath = "%s/etc/statistics.xml" % cf.get('server', 'repository')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            print "Could not read bcfg2.conf; exiting"
            raise SystemExit, 1
    try:
        statsdata = XML(open(statpath).read())
    except (IOError, XMLSyntaxError):
        print("StatReports: Failed to parse %s"%(statpath))
        raise SystemExit, 1

    if not clientpath:
        try:
            clientspath = "%s/Metadata/clients.xml" % \
                          cf.get('server', 'repository')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            print "Could not read bcfg2.conf; exiting"
            raise SystemExit, 1
    try:
        clientsdata = XML(open(clientspath).read())
    except (IOError, XMLSyntaxError):
        print("StatReports: Failed to parse %s"%(clientspath))
        raise SystemExit, 1

    load_stats(clientsdata, statsdata, verb)
