"""
Modifying AST with `srcml`. Parses very OK! Can we modify??
"""

import copy
import logging
import os
import re
import subprocess
from pathlib import Path

from lxml import etree
from lxml.builder import ElementMaker

logger = logging.getLogger(__name__)

srcml_install = Path(__file__).parent / 'srcml'
srcml_exe = srcml_install / 'bin/srcml'
assert srcml_exe.exists()

srcml_env = copy.deepcopy(os.environ)
if "LD_LIBRARY_PATH" in srcml_env:
    srcml_env["LD_LIBRARY_PATH"] = str(srcml_install / 'lib') + ':' + srcml_env["LD_LIBRARY_PATH"]
else:
    srcml_env["LD_LIBRARY_PATH"] = str(srcml_install / 'lib')

namespaces = {'src': 'http://www.srcML.org/srcML/src'}
E = ElementMaker(namespace=namespaces["src"], nsmap=namespaces)


# Print XML from root
def prettyprint(node, return_string=False):
    s = etree.tostring(node, encoding="unicode", pretty_print=True)
    if return_string:
        return s
    else:
        print(s)


# prettyprint(xmldata)


def tagname(node):
    return etree.QName(node).localname


def start_pos(node):
    # prettyprint(node)
    return node.get('{http://www.srcML.org/srcML/position}start')


def get_space(node, front_back):
    if front_back == 'front':
        regex = rf'^<{etree.QName(node).localname}[^>]+>(\s+)'
    elif front_back == 'back':
        regex = r'(\s+)$'
    else:
        raise
    m = re.search(regex, etree.tostring(node, encoding='unicode'))
    if m:
        return m.group(1)
    else:
        return ''


class SrcMLInfo:
    def __init__(self, c_code=None):
        self.c_code = c_code
        self.xml = None
        self.xml_root = None
        self.load_xml()

    def load_xml(self):
        proc = subprocess.Popen([str(srcml_exe), '-lC'],
                                stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        channel = proc.communicate(input=self.c_code.encode('utf-8'))
        if proc.returncode != 0:
            raise Exception(channel[1])
        self.xml = channel[0]
        parser = etree.XMLParser(huge_tree=True)
        self.xml_root = etree.fromstring(self.xml, parser=parser)
        logger.debug('new XML:\n%s', self.xml.decode('utf-8'))
        return self.xml

    def load_c_code(self):
        proc = subprocess.Popen([str(srcml_exe)], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        self.c_code = proc.communicate(input=self.xml)[0].decode('utf-8')
        logger.debug('new C code:\n%s', self.c_code)
        return self.c_code

    def revert_changes(self):
        self.xml_root = etree.fromstring(self.xml)

    def apply_changes(self):
        self.xml = etree.tostring(self.xml_root)

    def xp(self, *args):
        if len(args) == 1:
            node = self.xml_root
            query = args[0]
        else:
            node = args[0]
            query = args[1]
        return node.xpath(query, namespaces=namespaces)

    @classmethod
    def tag(cls, node):
        return etree.QName(node).localname
