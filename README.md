openstack
=========

Various OpenStack tools and files...

scanner.py
----------

Run this and pass in a source code directory (one level below the projeect root, so it doesn't try to examine .tox directory and other areas) and it will do the following things...

First, it will look at each .py file and extract the Neutron imports in the file. Next, it will look at the places in the file where the import is used and collect up the name (method, variable, etc).

As output, it will show each of the neutron files imported for the source file, along with the actual references. You can specify to have the output go to a file, by using the -o options.

If you specify the -s option, after all source files have been processed, the script will then print out all the neutron modules imported, along with a list of references used in each of the modules. If the -o option was used, the summary output will be in a file with same name, and a '.summary' suffix.

The script will handle the case where an import has aliases, and imports where the method (e.g. i18n _LE) is specified in the import line. There is a test_scanner.py file that has unit tests for the script to cover the important bits (not the reporting).

If you don't specify a root directory, it will use the current directory (so run it from /opt/stack/neutron/neutron, for example).

Example:

<pre>
$ cd /opt/stack/neutron-vpnaas/neutron_vpnaas/services/vpn
$ python ~/openstack/scanner.py device_drivers -s
Analysis for device_drivers/ipsec.py
    ...
    neutron/i18n.py
        _LE
    neutron/openstack/common/loopingcall.py
        FixedIntervalLoopingCall
    neutron/plugins/common/constants.py
        ACTIVE
        DOWN
        ERROR
...
Analysis for device_drivers/cisco_csr_rest_client.py
    neutron/i18n.py
        _LE
        _LW
Analysis for device_drivers/strongswan_ipsec.py
    neutron/agent/linux/ip_lib.py
        IPWrapper
    neutron/plugins/common/constants.py
        ACTIVE
        DOWN
...

Summary of neutron import usage
    neutron/agent/linux/ip_lib.py
        IPWrapper
    neutron/agent/linux/utils.py
        replace_file
    neutron/api/v2/attributes.py
        _validate_ip_address
    neutron/common/exceptions.py
        NeutronException
    neutron/common/rpc.py
        create_connection
        get_client
    neutron/i18n.py
        _LE
        _LI
        _LW
    neutron/openstack/common/loopingcall.py
        DynamicLoopingCall
        FixedIntervalLoopingCall
    neutron/openstack/common/periodic_task.py
        PeriodicTasks
        periodic_task
    neutron/plugins/common/constants.py
        ACTIVE
        DOWN
        ERROR
    neutron/plugins/common/utils.py
        in_pending_status
</pre>

json-out.py
-----------
Created a quick Python script that takes a (Neutron) command line with --verbose flag turned on, and generates a pretty printed output of the JSON for the request and response messages, so that this can be included into API documentation. The script, called json-out.py, is my GitHub openstack repo. Here are the options to the script:

<pre>
Usage: json-out.py [options] -- command to run with verbose flag enabled
 
Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -H, --HEADERS         Show all headers
  -o, --output          Show command output
  -d, --debug           Show debug output
  -a, --auth            Show authentication messages and headers
  -f FILE, --filename=FILE
                        Save JSON to file(s) with prefix specified
</pre>

The -o option will show the normal stdout from the command, whereas the -d option will show the stderr output, including debug logging from the --verbose flag you provide. If you want to see all header fields from the messages, you can use the -H option. If you also want to see the authorization messages and auth token (PSK), use the -a option.

You can choose to have all JSON output go to a file with the prefix you specify, _req or _res for request and result JSON messages, a instance number for cases where more than one request/result would occur (e.g. auth messages and then create messages), and .json suffix.

IMPORTANT NOTES:

- You must use a double dash to separate the options for the script from the command and options to run. 
- You also must have the desired user credentials set (e.g source openrc admin) for the commands you want to issue.
- You must include --verbose in the Neutron command to see the JSON output.
- This is geared for Neutron, but probably will work with other components, if they have an option to perform.  Here's an example:

<pre>
openstack@devstack-32:~/devstack$ python ../openstack/json-out.py -- neutron --verbose vpn-ikepolicy-create ikepolicy1
 
JSON
REQUEST
POST /v2.0/vpn/ikepolicies.json
User-Agent: python-neutronclient
Accept: application/json
 
{
  "ikepolicy": {
    "phase1_negotiation_mode": "main", 
    "auth_algorithm": "sha1", 
    "name": "ikepolicy1", 
    "encryption_algorithm": "aes-128", 
    "pfs": "group5", 
    "ike_version": "v1"
  }
}
 
 
RESPONSE
{
  "date": "Tue, 13 Aug 2013 12:07:58 GMT", 
  "status": "201", 
  "content-length": "334", 
  "content-type": "application/json; charset=UTF-8"
}
{
  "ikepolicy": {
    "name": "ikepolicy1", 
    "tenant_id": "26de9cd6cae94c8cb9f79d660d628e1f", 
    "auth_algorithm": "sha1", 
    "encryption_algorithm": "aes-128", 
    "pfs": "group5", 
    "phase1_negotiation_mode": "main", 
    "lifetime": {
      "units": "seconds", 
      "value": 3600
    }, 
    "ike_version": "v1", 
    "id": "771f081c-5ec8-4f9a-b041-015dfb7fbbe2", 
    "description": ""
  }
}
</pre>
