from srcml import SrcMLInfo


def test_srcml_info():
    c_code = '''int main()
{
    return 1;
}
'''
    info = SrcMLInfo(c_code)
    expected_xml_code = b'''
'''
    expected_xml_code = (b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<unit xmlns="http://www.srcML.org/srcML/src" revision="1.0.0" language="C"><function><type><name>int</name></type> <name>main</name><parameter_list>()</parameter_list>
<block>{<block_content>
    <return>return <expr><literal type="number">1</literal></expr>;</return>
</block_content>}</block></function>
</unit>
''')
    assert info.xml == expected_xml_code
