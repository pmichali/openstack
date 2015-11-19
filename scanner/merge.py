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

from __future__ import print_function

import argparse
import collections
import sys

def gather_references(a_file, references, output_file):
    print("Processing File:", a_file, file=output_file)
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


def get_exclusions(exclusion_file):
    if exclusion_file is None:
        return []
    with open(exclusion_file) as contents:
        exclusions = contents.readlines()
    return [ex.strip() for ex in exclusions]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge summary file(s)')
    parser.add_argument('-e', '--exclude', dest='exclude', action='store',
                        help='File of modules that have been processed '
                        'already and should be excluded')
    parser.add_argument('-o', '--output', dest='output', action='store',
                        help='Redirect output to file specified')
    parser.add_argument('summary_files', metavar='FILE', nargs='+',
                        help='Summary files to merge')
    args = parser.parse_args()

    if args.output:
        output_file = open(args.output, 'w')
    else:
        output_file = sys.stdout

    references = collections.defaultdict(set)
    for a_file in args.summary_files:
        gather_references(a_file, references, output_file)

    exclusions = get_exclusions(args.exclude)
    trimmed_references = [(k,v) for k,v in references.items()
                          if k not in exclusions]

    sorted_refs = collections.OrderedDict(
        sorted(trimmed_references, key=lambda t: t[0]))
    for module_path, refs in sorted_refs.iteritems():
        print("    " + module_path, file=output_file)
        for ref in sorted(refs, key=lambda s: s.lower()):
            print("        " + ref, file=output_file)
