import os
import sys

# this allows the CalCore package to be installed as a Zope product.
# It will add the src directory to the PYTHONPATH
product_dir, filename = os.path.split(__file__)
src_path = os.path.join(product_dir, 'src')
sys.path.append(src_path)

# make sure iCalendar is on the PYTHON PATH
try:
    # this puts iCalendar/src on the PYTHONPATH
    from Products import iCalendar
except ImportError:
    # it should be placed on the PYTHONPATH some other way then by
    # the user, such as by zope.conf
    pass

def initialize(context):
    pass
