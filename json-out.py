"""
Process a neutron command and output request(s)/response(s) in JSON

Runs command and displays the relevent headers and JSON output, for the
request and/or response, depending on the operation. If there are errors,
they are displayed. Options allow the raw debug output, normal user output
of the command, viewing of all headers, and viewing of auth headers and
messages.

The JSON can be sent to files with a user provided prefix, and a .json
suffix. Requests will have "req" before the suffix, and responses will
have "res". Multiple pairs will be numbered.

You must use double-dash to separate options from the command and its
arguments. You must also specify the command option to generated JSON
output, which for neutron is "--verbose".

Example:
    pcm@ubuntu[3731] $ python json-out.py -- neutron --verbose router-list

    JSON
    REQUEST
    GET /v2.0/routers.json
    User-Agent: python-neutronclient
    Accept: application/json

    RESPONSE
    {
      "date": "Thu, 08 Aug 2013 15:13:25 GMT", 
      "status": "200", 
      "content-length": "289", 
      "content-type": "application/json; charset=UTF-8", 
      "content-location": "http://172.16.6.148:9696/v2.0/routers.json"
    }
    {
      "routers": [
        {
          "status": "ACTIVE", 
          "external_gateway_info": {
            "network_id": "7e540934-4053-4729-993e-a912a2a1b65a", 
            "enable_snat": true
          }, 
          "name": "router1", 
          "admin_state_up": true, 
          "tenant_id": "f600e82d8b324979bb412d5e655cf0ee", 
          "routes": [], 
          "id": "6bed56d5-4fad-4a5e-801c-22c06cac64db"
        }
      ]
    }
"""

import optparse
from itertools import izip
import json
import re
import subprocess
import sys


request_response_re = re.compile(r'(REQ|RESP):(.+)')
errors_re = re.compile(r'(ERROR: .+|\S+: error: .+)')

request_info_re = re.compile(r'curl -i \S+(/v2.0/\S+) -X (\S+) (.+)')
headers_re = re.compile(r'\s*-H "(\S+): (\S+)"')
params_re = re.compile(r"-d \'([^\']+)\'")

response_info_re = re.compile(r"({[^}]+})(.*)")


class InvalidInputException(Exception):
    pass

def strip_trailing_whitespace(multi_string):
    stripped = [m.rstrip() for m in multi_string.split('\n')]
    return '\n'.join(stripped)

def extract_request(info):
    m = request_info_re.search(info)
    if m:
        relative_url = m.group(1)
        request_type = m.group(2)

        headers_dict = dict(headers_re.findall(info))
        if opts.show_all_headers:
            headers = headers_dict
        else:
            headers = ('User-Agent', 'Accept')
        if not opts.show_auth and 'X-Auth-Token' in headers:
            del headers['X-Auth-Token']
        filtered_headers = ["%s: %s" % (k,headers_dict[k])
                            for k in headers]

        req_params = params_re.search(info)
        if req_params:
            json_output = json.dumps(json.loads(req_params.group(1)), indent=2)
            req_json = strip_trailing_whitespace(json_output)
        else:
            req_json = None
        return request_type, relative_url, filtered_headers, req_json
    else:
        raise InvalidInputException("Unable to parse request: %s" % info)

def extract_response(info):
    m = response_info_re.search(info)
    if m:
        stat_response = m.group(1).replace("'", '"')
        json_output = json.dumps(json.loads(stat_response), indent=2)
        json_status_response = strip_trailing_whitespace(json_output)
        response = m.group(2).strip()
        if response != '':
            json_output = json.dumps(json.loads(response), indent=2)
            json_info_response = strip_trailing_whitespace(json_output)
        else:
            json_info_response = "[None]"
        return "%s\n%s\n" % (json_status_response, json_info_response)
    else:
        raise InvalidInputException("Unable to parse response: %s" % info)

def print_info_from_pairs(raw_list):
    print "\nJSON"
    instance = 0
    for request, response in izip(raw_list[::2], raw_list[1::2]):
        operation, info = request
        if operation != 'REQ':
            raise InvalidInputException("Missing expected request")
        
        request_type, url, headers, request_json = extract_request(info)
        if not opts.show_auth and '/v2.0/token' in url:
            continue # Don't care about authentication request/response
        
        operation, info = response
        if operation != 'RESP':
            raise InvalidInputException("Missing expected response")
        response_json = extract_response(info)
        
        print "REQUEST\n%s %s" % (request_type, url)
        print '\n'.join(headers)
        if request_json:
            print '\n%s\n\n' % request_json
            if opts.filename:
                name = "%s_req%s.json" % (opts.filename,
                                          str(instance) if instance > 0 else "")
                with open(name, "w") as f:
                    f.write(request_json)
                    f.write('\n')
        print '\nRESPONSE\n%s\n\n' % response_json
        if opts.filename:
            name = "%s_res%s.json" % (opts.filename,
                                      str(instance) if instance > 0 else "")
            with open(name, "w") as f:
                f.write(response_json)
                f.write('\n')
            instance += 1
        
        

def find_requests_and_responses(lines):
    return request_response_re.findall(lines)

def find_errors(lines):
    return errors_re.findall(lines)

def collect_output_from_file(filename):
    with open(filename) as f:
        contents = f.read()
    return contents

def collect_output_from_command(cmd):
    """Run command with verbose and return only the stderr output.

    Command should include --verbose, so that the REST request and response
    output is produced (and sent to stderr). Will only return that info.
    It is assumed that the authentication for the user has already been
    established (e.g. source openrc).
    """
    
    try:
        # print "Trying %s" % ' '.join(sys.argv[1:])
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output, err_msgs = p.communicate()
    except OSError as err:
        print("Failed running '%s' (%d - %s)" %
              (sys.argv, err.errno, err.strerror))
        raise
    else:
        return output, err_msgs

if __name__ == '__main__':
    usage = "usage: %prog [options] -- command to run with verbose flag enabled"
    
    parser = optparse.OptionParser(usage=usage, version="%prog 1.1")
    parser.add_option('-H', "--HEADERS", action='store_true', default=False,
                      dest='show_all_headers', help='Show all headers')
    parser.add_option('-o', "--output", action='store_true', default=False,
                      dest='show_output', help='Show command output')
    parser.add_option('-d', "--debug", action='store_true', default=False,
                      dest='show_debug_output', help='Show debug output')
    parser.add_option('-a', "--auth", action='store_true', default=False,
                      dest='show_auth',
                      help='Show authentication messages and headers')
    parser.add_option('-f', "--filename", dest="filename", metavar="FILE",
                      help='Save JSON to file(s) with prefix specified')

    opts,openstack_command = parser.parse_args()

    if len(openstack_command) == 0:
        print "No command provided to run...exiting.\n\n"
        sys.exit(0)
        
    normal_output, debug_lines = collect_output_from_command(openstack_command)
    operations = find_requests_and_responses(debug_lines)
    errors = find_errors(debug_lines)
    if errors:
        print "Command failed! Errors reported:"
        print '\n'.join(errors)
        sys.exit(1)

    if opts.show_debug_output:
        print "\nDEBUG OUTPUT:\n"
        print debug_lines
    if opts.show_output:
        print "\nCOMMAND OUTPUT:\n"
        print normal_output
    print_info_from_pairs(operations)
