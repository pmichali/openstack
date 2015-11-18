# Copyright 2015 Paul Michali.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
import sys

def gather_references(a_file, references):
    print "Processing File:", a_file
    with open(a_file) as contents:
        for line in contents:
            item = line.strip()
            if item == '':
                continue
            if item.startswith('Summary'):
                continue
            if item.startswith('neutron/'):
                module_path = item
                continue
            references[module_path].add(item)
            
if __name__ == '__main__':
    references = collections.defaultdict(set)
    for a_file in sys.argv[1:]:
        gather_references(a_file, references)
    sorted_refs = collections.OrderedDict(
        sorted(references.items(), key=lambda t: t[0]))
    for module_path, refs in sorted_refs.iteritems():
        print("    " + module_path)
        for ref in refs:
            print("        " + ref)
