# -*- coding: utf-8 -*-
"""
Tests for the ullekhanam_db interface and the associated schema classes.
"""

from __future__ import absolute_import

import logging
import os
import pytest
import jsonschema
import tests
from sanskrit_data.schema import ullekhanam, common, books, users

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


# Used in the tests below
class TestClass(common.JsonObject):
    def __init__(self, field1):
        self.field1 = field1


def test_serialization():
    testObj = TestClass(field1=21)
    testObj.dump_to_file(filename=os.path.join(TEST_DATA_DIR, "testObj.json"))
    testObj2 = testObj.read_from_file(filename=os.path.join(TEST_DATA_DIR, "testObj.json"), name_to_json_class_index={"TestClass": TestClass})
    assert testObj.field1 == testObj2.field1