#!/usr/bin/env python

"""
<Program Name>
  test_init.py

<Author> 
  Vladimir Diaz

<Started>
  March 30, 2015. 

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test cases for __init__.py (mainly the exceptions defined there).
"""

# Help with Python 3 compatibility, where the print statement is a function, an
# implicit relative import is invalid, and the '/' operator performs true
# division.  Example:  print 'hello world' raises a 'SyntaxError' exception.
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import unittest
import logging

import tuf
import tuf.log

logger = logging.getLogger('tuf.test_init')

class TestInit(unittest.TestCase):
  def setUp(self):
    pass


  def tearDown(self):
    pass


  def test_bad_signature_error(self):
    bad_signature_error = tuf.BadSignatureError('bad_role')
    logger.error(bad_signature_error)


  def test_slow_retrieval_error(self):
    slow_signature_error = tuf.SlowRetrievalError('bad_role')
    logger.error(slow_signature_error)


  def test_bad_hash_error(self):
    bad_hash_error = tuf.BadHashError('01234', '56789')
    logger.error(bad_hash_error)


  def test_invalid_metadata_json_error(self):
    format_error = tuf.FormatError('Improperly formatted JSON')
    invalid_metadata_json_error = tuf.InvalidMetadataJSONError(format_error)
    logger.error(invalid_metadata_json_error)
  

  
# Run the unit tests.
if __name__ == '__main__':
  unittest.main()
