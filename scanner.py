import fnmatch
import operator
import os
import re
import sys

if len(sys.argv) == 1:
    root = '.'
else:
    root = sys.argv[1]

import_re = re.compile(r'import\s+(neutron\.\S+)')
from_re = re.compile(r'from\s+(neutron\.\S+)\s+import\s+([^#]+)')
import_as_re = re.compile(r'import\s+(neutron\.\S+)\s+as\s+(\S+)')
from_as_re = re.compile(r'from\s+(neutron\.\S+)\s+import\s+(\S+)\s+as\s+(\S+)')
from_line_one_re = re.compile(r'from\s+(neutron\.\S+)\s+import\s+\(')
from_line_two_re = re.compile(r'\s+(\S+)\s*\)')
from_as_line_two_re = re.compile(r'\s+(\S+)\s+as\s+(\S+)\s*\)')

NEUTRON_BASE = '/opt/stack/neutron/'


class NeutronModuleNotFound(Exception):

    message = "Unable to find Neutron module '%(name)s'"

    def __init__(self, **kwargs):
        self.msg = self.message % kwargs
        super(NeutronModuleNotFound, self).__init__(self.msg)


def gen_find(file_pattern, top):
    for path, dirlist, filelist in os.walk(top):
        for name in fnmatch.filter(filelist, file_pattern):
            yield os.path.join(path, name)


def gen_open(filenames):
    for name in filenames:
        yield open(name)


def gen_parse(a_file):
    continued_base = ''
    for line in a_file:
        # Try continued line imports first
        if continued_base:
            base = continued_base
            continued_base = ''
            m = from_as_line_two_re.match(line)
            if m:
                target = m.group(1)
                alias = m.group(2)
            else:
                m = from_line_two_re.match(line)
                if m:
                    target = m.group(1)
                    alias = target.split('.')[-1]
            if m:
                yield True, base + '.' + target, alias
            else:
                print "Parse error:", line
            continue
        m = from_line_one_re.match(line)
        if m:
            continued_base = m.group(1)
            continue
        # Next check 'as' versions, so no ambiguity
        m = import_as_re.match(line)
        if m:
            target = m.group(1)
            alias = m.group(2)
            yield True, target, alias
            continue
        m = from_as_re.match(line)
        if m:
            base = m.group(1)
            target = m.group(2)
            alias = m.group(3)
            yield True, base + '.' + target, alias
            continue
        # These must be last, so they don't trigger on other variants
        m = import_re.match(line)
        if m:
            target = m.group(1)
            alias = target.split('.')[-1]
            yield True, target, alias
            continue
        m = from_re.match(line)
        if m:
            base = m.group(1)
            targets = m.group(2).split(',')
            for target in targets:
                target = target.strip()
                alias = target.split('.')[-1]
                yield True, base + '.' + target, alias
            continue
        yield False, line, None


class NeutronModule(object):

    def __init__(self, name):
        self.dotted_name = name
        self.name = name.replace('.', '/') + ".py"
        self.refs = set()
        if not os.path.isfile(os.path.join(NEUTRON_BASE, self.name)):
            # Assume this is an object in the module
            parts = name.split('.')
            alias = parts.pop()
            self.dotted_name = '.'.join(parts)
            self.name = '/'.join(parts) + ".py"
            if not os.path.isfile(os.path.join(NEUTRON_BASE, self.name)):
                raise NeutronModuleNotFound(name=name)
            self.add_usage(alias)

    def add_usage(self, reference):
        self.refs.add(reference)


class ImportAlias(object):

    def __init__(self, name, for_module):
        self.name = name
        self.regex = self.make_usage_regex(name)
        self.module_name = for_module

    @classmethod
    def make_usage_regex(cls, alias):
        return re.compile(r'[^\w.]' + alias + r'\.([a-zA-Z0-9_.]+)')


class SourceScanner(object):

    def __init__(self, name):
        self.known_aliases = {}
        self.imported_modules = {}
        self.name = name

    def add_import(self, alias, module_name):
        new_module = NeutronModule(module_name)
        module_name = new_module.dotted_name
        if module_name in self.imported_modules:
            self.imported_modules[module_name].refs |= new_module.refs
        else:
            self.imported_modules[module_name] = new_module
        self.known_aliases[alias] = ImportAlias(alias, module_name)

    def find_import_usage(self, line):
        for alias_info in self.known_aliases.values():
            m = alias_info.regex.findall(line)
            module = self.imported_modules[alias_info.module_name]
            for match in m:
                module.add_usage(match)

    def report_for_source_module(self):
        print "Analysis for", self.name
        report_modules(self.imported_modules)

    def analyze(self):
        with open(self.name) as o:
            parsed_lines = gen_parse(o)
            for is_import, content, name in parsed_lines:
                if is_import:
                    self.add_import(name, content)
                else:
                    self.find_import_usage(content)


def report_modules(modules):
    for module in sorted(modules.values(),
                         key=lambda a: a.dotted_name):
        print "    " + module.name
        for ref in sorted(module.refs):
            print "        %s" % ref


def process_references(from_root):
    files = gen_find("*.py", from_root)
    all_references = {}
    for f in files:
        source_scan = SourceScanner(f)
        source_scan.analyze()
        source_scan.report_for_source_module()
        for module in source_scan.imported_modules.values():
            if module.dotted_name in all_references:
                all_references[module.dotted_name].refs |= module.refs
            else:
                all_references[module.dotted_name] = module
    print "\n\nSummary of neutron import usage"
    report_modules(all_references)


if __name__ == '__main__':
    process_references(root)
