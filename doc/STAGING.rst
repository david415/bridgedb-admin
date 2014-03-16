# -*- coding: utf-8 ; mode: rst ; -*-

Staging a Test Instance of BridgeDB
===================================

A test instance of BridgeDB can be staged on ponticum.torproject.org, at the
url https://bridges-test.torproject.org. The `etc/test-bridgedb.conf` file,
which contains the configuration for the staging server should have its HTTP
server listening on port `7357` (`test` in leetspeak), and the email server
should listen on port `7257`. Apache and postfix are already configured to
foward requests to the `bridges-test.torproject.org` domain to these ports.

In the `bin/` directory, you'll find the `test-deploy` and `test-run-bridgedb`
scripts, which can be used to deploy the staging servers. These scripts deploy
BridgeDB from the same git checkout as the normal deployment scripts, so
you'll first need to go into the `bridgedb` user's home directory and checkout
the version or commit of BridgeDB that you would like to stage::

    torsocks ssh ponticum.torproject.org
    sudo -u -i bridgedb
    cd ./bridgedb
    git fetch origin
    git checkout [STAGE_VERSION]
..

Next, to deploy the staging servers, do::

    /srv/bridges.torproject.org/home/bridges-test.torproject.org/bin/test-deploy
..

The staging server should now be running. Unless you changed the file at
`/srv/bridges.torproject.org/home/bridges-test.torproject.org/etc/test-bridgedb.conf`,
its logfiles should be located at
`/srv/bridges.torproject.org/home/bridges-test.torproject.org/log/bridgedb.log`::

    tail -f /srv/bridges.torproject.org/home/bridges-test.torproject.org/log/bridgedb.log
..

Apache Vhost Configuration
--------------------------

.. note:: This is already done for you! This section exists merely to document
          what must be done should the apache configuration need to be changed.

::
 12:43 <isis> weasel: it seems there is a 'bridges-test.torproject.org' ServerAlias for bridgedb in
              ponticum.torproject.org:/etc/apache2/sites-staging/bridges.torproject.org… if i were to set up a staging
              instance of BridgeDB, do you have a recommended or preferred way for me to do that?
 14:17 <weasel> isis: we can create a second, different vhost, and proxypass that to a different port.
 14:45 <isis> weasel: could you do that such that bridges-test.torproject.org points to port 7357, please?
 14:53 <weasel> isis: sure.  (if you're in the bridges group so could you I think.)
 14:54 <weasel> at least the apache part.  not the dns part
 14:55 <weasel> there
 14:55 <nsa> tor-internal: Peter Palfrader <peter@palfrader.org>: 2014-01-17 14:55:26 [domains/master]: Add bridges-test
 15:22 <weasel> you can edit sites-staging/$foo, then run apache2-update-vhost briges.torproject.org
 15:22 <weasel> (the latter using sudo)
::
