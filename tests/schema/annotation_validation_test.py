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


def test_ImageAnnotation_source_auto_set(db_fixture):
    db = db_fixture
    book_portion = books.BookPortion.from_details(
        title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha")
    updated_book = book_portion.update_collection(db)
    target_page_id = updated_book._id
    annotation = ullekhanam.ImageAnnotation()
    annotation.targets=[
        ullekhanam.ImageTarget.from_details(container_id=str(target_page_id),
                                            rectangle=ullekhanam.Rectangle.from_details())]

    # logging.debug(annotation.to_json_map())

    updated_annotation = annotation.update_collection(db_interface=db)
    # logging.debug("update result is " + str(updated_annotation))
    assert(updated_annotation.source.jsonClass == "DataSource")

