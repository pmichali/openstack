import os


import mock
from oslo_log import log as logging

from neutron_vpnaas.tests import base
from neutron_vpnaas import scanner

LOG = logging.getLogger(__name__)


# NOTE: This was created to run under the VPN repo. Placed the source in the
# neutron_vpnaas/ area, and this test file in neutron_vpnaas/tests/unit/.
#
# Run the test with:
#    tox -e py27 -- neutron_vpnaas.tests.unit.test_scanner

class TestImportParsing(base.BaseTestCase):

    def test_import(self):
        content = """import neutron.x.y1
import neutron.y2 # comment
"""
        lines = scanner.gen_parse(content.splitlines())
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.x.y1', content)
        self.assertEqual('y1', alias)
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.y2', content)
        self.assertEqual('y2', alias)

    def test_import_as(self):
        content = """import neutron.x.y1 as y
import neutron.y2 as z # comment
"""
        lines = scanner.gen_parse(content.splitlines())
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.x.y1', content)
        self.assertEqual('y', alias)
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.y2', content)
        self.assertEqual('z', alias)

    def test_from_import(self):
        content = """from neutron.x import y1
from neutron.w.x import y2 # comment
"""
        lines = scanner.gen_parse(content.splitlines())
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.x.y1', content)
        self.assertEqual('y1', alias)
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.w.x.y2', content)
        self.assertEqual('y2', alias)

    def test_from_import_as(self):
        content = """from neutron.x import y1 as y
from neutron.w.x import y2 as z # comment
"""
        lines = scanner.gen_parse(content.splitlines())
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.x.y1', content)
        self.assertEqual('y', alias)
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.w.x.y2', content)
        self.assertEqual('z', alias)

    def test_multiple_from_imports_on_one_line(self):
        content = """from neutron.x import y1, y2, y3
"""

        lines = scanner.gen_parse(content.splitlines())
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.x.y1', content)
        self.assertEqual('y1', alias)
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.x.y2', content)
        self.assertEqual('y2', alias)
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.x.y3', content)
        self.assertEqual('y3', alias)

    def test_from_import_multiline(self):
        content = """from neutron.x import (
    y1)
from neutron.w.x import ( 
    y2 )
"""
        lines = scanner.gen_parse(content.splitlines())
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.x.y1', content)
        self.assertEqual('y1', alias)
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.w.x.y2', content)
        self.assertEqual('y2', alias)

    def test_from_import_as_multiline(self):
        content = """from neutron.x import (
    y1 as y)
from neutron.w.x import ( 
    y2 as z )  # comment
"""

        lines = scanner.gen_parse(content.splitlines())
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.x.y1', content)
        self.assertEqual('y', alias)
        is_import, content, alias = next(lines)
        self.assertTrue(is_import)
        self.assertEqual('neutron.w.x.y2', content)
        self.assertEqual('z', alias)

class TestImportUsage(base.BaseTestCase):

    def setUp(self):
        super(TestImportUsage, self).setUp()
        mock.patch.object(os.path, 'isfile', return_value=True).start()
        self.source_scanner = scanner.SourceScanner('test.py')
        self.source_scanner.add_import('y1', 'neutron.x.y')
        self.module = self.source_scanner.imported_modules[
            self.source_scanner.known_aliases['y1'].module_name]

    def test_found_method(self):
        self.source_scanner.find_import_usage('    y1.bar(1,2,3)')
        self.assertEqual(set(['bar']), self.module.refs)

    def test_found_attribute(self):
        self.source_scanner.find_import_usage('    y1.bar = 5')
        self.assertEqual(set(['bar']), self.module.refs)

    def test_found_dict(self):
        self.source_scanner.find_import_usage('    y1.bar[123] = 4')
        self.assertEqual(set(['bar']), self.module.refs)

    def test_found_class(self):
        self.source_scanner.find_import_usage('    y1.SomeClass(1)')
        self.assertEqual(set(['SomeClass']), self.module.refs)

    def test_found_object_attribute(self):
        self.source_scanner.find_import_usage('    y1.some_object.some_attr = 4')
        self.assertEqual(set(['some_object.some_attr']), self.module.refs)

    def test_found_imbedded(self):
        self.source_scanner.find_import_usage("    x = {y1.z: 4, 'func': foo(y1.x), 'pos': ray[y1.index]")
        self.assertEqual(set(['index', 'x', 'z']), self.module.refs)

    def test_found_duplicates(self):
        self.source_scanner.find_import_usage("    y1.x = y1.y + y1.x")
        self.assertEqual(set(['x', 'y']), self.module.refs)

    def test_not_matching(self):
        self.source_scanner.find_import_usage("  not_y1.x = yy1.z + x.y1.t")
        self.assertEqual(set(), self.module.refs)


class TestImportDetection(base.BaseTestCase):

    """Note: Tests in this class require real modules."""

    def test_neutron_module(self):
        module = scanner.NeutronModule('neutron.common.config')
        self.assertEqual('neutron/common/config.py', module.name)
        self.assertEqual(set(), module.refs)

    def test_object_sepcified_neutron_module(self):
        module = scanner.NeutronModule('neutron.i18n._LE')
        self.assertEqual('neutron/i18n.py', module.name)
        self.assertEqual(set(['_LE']), module.refs)

    def test_create_alias_and_module_for_import(self):
        expected_module = 'neutron.common.config'
        expected_alias = 'setup_logging'
        source_scanner = scanner.SourceScanner('source.py')
        source_scanner.add_import(expected_alias, expected_module)
        aliases = source_scanner.known_aliases
        modules = source_scanner.imported_modules
        self.assertIn(expected_alias, aliases)
        self.assertEqual(expected_module, aliases[expected_alias].module_name)
        self.assertIn(expected_module, modules)
        self.assertEqual(expected_module,
                         modules[expected_module].dotted_name)
        self.assertEqual('neutron/common/config.py',
                         modules[expected_module].name)
        self.assertEqual(set(), modules[expected_module].refs)

    def test_import_directory(self):
        expected_module = 'neutron.extensions'
        expected_alias = 'extensions'
        source_scanner = scanner.SourceScanner('source.py')
        source_scanner.add_import(expected_alias, expected_module)
        aliases = source_scanner.known_aliases
        modules = source_scanner.imported_modules
        self.assertIn(expected_alias, aliases)
        self.assertEqual(expected_module, aliases[expected_alias].module_name)
        self.assertIn(expected_module, modules)
        self.assertEqual(expected_module,
                         modules[expected_module].dotted_name)
        self.assertEqual('neutron/extensions',
                         modules[expected_module].name)
        self.assertEqual(set(), modules[expected_module].refs)

    def test_create_alias_and_module_for_object_import(self):
        expected_alias = '_LE'
        source_scanner = scanner.SourceScanner('source.py')
        source_scanner.add_import(expected_alias, 'neutron.i18n._LE')
        expected_module = 'neutron.i18n'
        aliases = source_scanner.known_aliases
        modules = source_scanner.imported_modules
        self.assertIn(expected_alias, aliases)
        self.assertEqual(expected_module, aliases[expected_alias].module_name)
        self.assertIn(expected_module, modules)
        self.assertEqual(expected_module,
                         modules[expected_module].dotted_name)
        self.assertEqual('neutron/i18n.py', modules[expected_module].name)
        self.assertEqual(set([expected_alias]), modules[expected_module].refs)

    def test_create_alias_and_module_for_multiple_objects(self):
        expected_alias1 = '_LE'
        expected_alias2 = '_LW'
        source_scanner = scanner.SourceScanner('source.py')
        source_scanner.add_import(expected_alias1, 'neutron.i18n._LE')
        source_scanner.add_import(expected_alias2, 'neutron.i18n._LW')
        expected_module = 'neutron.i18n'
        aliases = source_scanner.known_aliases
        modules = source_scanner.imported_modules
        self.assertIn(expected_alias1, aliases)
        self.assertIn(expected_alias2, aliases)
        self.assertEqual(expected_module, aliases[expected_alias1].module_name)
        self.assertEqual(expected_module, aliases[expected_alias2].module_name)
        self.assertIn(expected_module, modules)
        self.assertEqual(expected_module,
                         modules[expected_module].dotted_name)
        self.assertEqual('neutron/i18n.py', modules[expected_module].name)
        self.assertEqual(set([expected_alias1, expected_alias2]),
                         modules[expected_module].refs)


class TestMiscellaneous(base.BaseTestCase):

    def test_exception(self):
        try:
            raise scanner.NeutronModuleNotFound(name="foo")
        except Exception as e:
            self.assertEqual("Unable to find Neutron module 'foo'",
                             e.msg)
        else:
            self.fail("Expected exception did not occur")
