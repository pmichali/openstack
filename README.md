openstack
=========

Various OpenStack tools and files...


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
