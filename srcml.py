"""
Modifying AST with `srcml`. Parses very OK! Can we modify??
"""

from lxml import etree as et
from lxml.builder import ElementMaker
import subprocess
from pathlib import Path
import re
import os
import copy

srcml_install = Path('srcml')
srcml_exe = srcml_install / 'bin/srcml'
assert srcml_exe.exists()

srcml_env = copy.deepcopy(os.environ)
srcml_env["LD_LIBRARY_PATH"] = str(srcml_install / 'lib') + ':' + srcml_env["LD_LIBRARY_PATH"]
namespaces={'src': 'http://www.srcML.org/srcML/src'}
E = ElementMaker(namespace="http://www.srcML.org/srcML/src")


# Print XML from root
def prettyprint(node, return_string=False):
    s = et.tostring(node, encoding="unicode", pretty_print=True)
    if return_string:
        return s
    else:
        print(s)
# prettyprint(xmldata)

def xp(node, xpath):
    return node.xpath(xpath, namespaces=namespaces)
    
def tagname(node):
    return et.QName(node).localname

def start_pos(node):
    # prettyprint(node)
    return node.get('{http://www.srcML.org/srcML/position}start')

def get_space(node, front_back):
    if front_back == 'front':
        regex = rf'^<{et.QName(node).localname}[^>]+>(\s+)'
    elif front_back == 'back':
        regex = r'(\s+)$'
    else:
        raise
    m = re.search(regex, et.tostring(node, encoding='unicode'))
    if m:
        return m.group(1)
    else:
        return ''


# Functions for running srcml command.
def srcml(filepath):
    """Run srcml.
    If the filepath is a .c file, return xml tree as lxml ElementTree.
    If the filepath is an .xml file, return source code as a string."""
    assert filepath.exists()
    args = [srcml_exe, filepath]
    args = [str(a) for a in args]
    if filepath.suffix == '.c':
        args += ['--position']
    
    proc = subprocess.run(args, env=srcml_env, capture_output=True)
    if proc.returncode != 0:
        print('Error', proc.returncode)
        print(proc.stderr)
        return None
    if filepath.suffix == '.xml':
        return proc.stdout.decode('utf-8')
    elif filepath.suffix == '.c':
        # with open(str(filepath) + '.xml', 'wb') as f:
        #     f.write(proc.stdout)
        xml = et.fromstring(proc.stdout)
        return xml

def get_xml(c_code):
    tmp = Path('/tmp/code.c')
    with open(tmp, 'w') as f:
        f.write(c_code)
    return xp(srcml(tmp), '//src:unit')[0]

def get_xml_from_file(c_file):
    return xp(srcml(c_file), '//src:unit')[0]

def get_code(xml_root):
    tmp = Path('/tmp/code.xml')
    with open(tmp, 'w') as f:
        f.write(et.tostring(xml_root, encoding='unicode'))
    return srcml(tmp)

def test_srcml_coupler():
    fname = Path('tests/testbed/testbed.c')
    root = get_xml_from_file(fname)
    get_code(root)
    with open(fname) as f:
        root = get_xml(f.read())
        get_code(root)
