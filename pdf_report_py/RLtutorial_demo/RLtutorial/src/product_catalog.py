# coding=utf-8

import os
import StringIO
import urllib2
import base64
import pyRXPU
import preppy
import urllib2

from xml.sax.saxutils import escape, unescape
from rlextra.radxml.xmlutils import TagWrapper
from rlextra.radxml.html_cleaner import cleanInline
from rlextra.rml2pdf import rml2pdf

DATA_DIR = 'data'

class Product(object):
    "Empty class to hold parsed product attributes"
    pass

def fix(tag):
    "Apply fixes to their descriptive markup"
    src = unicode(tag)
    step1 = src.replace(u'\x82',u'&eacute;')
    step2 = unescape(step1)
    step3 = step2.encode('utf-8')
    return step3

def parse_catalog(filename):

    """Validate and parse XML.  This will complain if invalid

    We fully parse the XML and turn into Python variables, so that any encoding
    issues are confronted here rather than in the template
    """

    xml = open(filename).read()
    p = pyRXPU.Parser()
    tree = p.parse(xml)
    tagTree = TagWrapper(tree)
    request_a_quote = [109,110,4121,4122,4123]
    # we now need to de-duplicate; the query returns multiple rows with different images
    # in them.  if id is same, assume it's the same product.
    ids_seen = set()
    products = []
    for prodTag in tagTree:
        id = int(str(prodTag.ProductId1))   #extract tag content
        if id in ids_seen:
            continue
        else:
            ids_seen.add(id)
        prod = Product()
        prod.id = id
        prod.modelNumber = int(str(prodTag.ModelNumber))
        prod.archived = (str(prodTag.Archived) == 'true')
        prod.name = fix(prodTag.ModelName) + u"我是中文字体，可以显示出来吗？".encode(encoding='utf-8')
        prod.summary= fix(prodTag.Summary)
        prod.description= fix(prodTag.Description)
        if prod.modelNumber in request_a_quote:
            prod.price = "Call us on 01635 246830 for a quote"
        else:
            prod.price =  '&pound;' + str(prodTag.UnitCost)[0:len(str(prodTag.UnitCost))-2]
        if prod.archived:
            pass
        else:
            products.append(prod)
    products.sort(key=lambda x: x.modelNumber)
    return products

def create_pdf(catalog, template):
    """Creates PDF as a binary stream in memory, and returns it

    This can then be used to write to disk from management commands or crons,
    or returned to caller via Django views.
    """
    RML_DIR = 'rml'
    templateName = os.path.join(RML_DIR, template)
    template = preppy.getModule(templateName)
    namespace = {
        'products':catalog,
        'RML_DIR': RML_DIR
        }
    rml = template.getOutput(namespace)
    open(os.path.join(DATA_DIR,'latest.rml'), 'w').write(rml)
    buf = StringIO.StringIO()
    rml2pdf.go(rml, outputFileName=buf)
    return buf.getvalue()


def main():
    filename = os.path.join(DATA_DIR, 'products.xml')
    print '\n'+'#'*20
    print '\nabout to parse file: ', filename
    products = parse_catalog(filename)
    print 'file parsed OK \n'
    print "Trying to regenerate the check-list"
    try:
        pdf = create_pdf(products, 'checklist_template.prep')
        filename ='output/harwood_checklist_other.pdf'
        open(filename,'wb').write(pdf)
        print 'success! created %s' % filename, '\n'
    except Exception, e:
        print 'Check-list failed! Error:\n', e, '\n'

    print "Trying to regenerate the flyer"
    try:
        pdf = create_pdf(products, 'flyer_template.prep')
        filename ='output/harwood_flyer_other1.pdf'
        open(filename,'wb').write(pdf)
        print 'success! created %s' % filename
    except Exception, e:
        print e
    print '\n' + '#'*20 + '\n'


import datetime
import traceback


def test_main():
    today = datetime.datetime.today()
    today_str = today.strftime("%Y_%m_%d_%H_%M_%S")
    filename = os.path.join('output', 'products_'+today_str+'.pdf')
    print '\n'+'#'*20
    print '\nabout to get file: ', filename
    try:
        rml = open('rml/page5.prep', 'r').read()
        rml2pdf.go(rml, filename)
    except:
        trace_info = traceback.format_exc()
        print trace_info


def test_dynamic_main():
    today = datetime.datetime.today()
    today_str = today.strftime("%Y_%m_%d_%H_%M_%S")
    filename = os.path.join('output', 'products_'+today_str+'.pdf')
    print '\n'+'#'*20
    print '\nabout to get file: ', filename
    try:
        pro = {"name": u"出库单", "item": u"中文", "ss": 12}
        template = preppy.getModule('../rml/page9.prep')
        rml = template.getOutput({"pro": pro})
        rml2pdf.go(rml, filename)
    except:
        trace_info = traceback.format_exc()
        print trace_info

if __name__ == '__main__':
    # main()
    # test_main()
    test_dynamic_main()
