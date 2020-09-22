"""
Tests for the ullekhanam_db interface and the associated schema classes.
"""

from __future__ import absolute_import

import logging
import os
import pytest
import jsonschema

import sanskrit_data
import tests
import tests.db
from sanskrit_data.schema import ullekhanam, common, books, users
from sanskrit_data.schema.ullekhanam.sanskrit import SubantaAnnotation

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

@pytest.fixture(scope='module')
def db_fixture(request):
    return tests.db.ullekhanam_db_fixture(request=request)


def test_import_export(db_fixture):
  db_fixture.import_all(rootdir=os.path.join(os.path.dirname(tests.db.__file__), "textract-example-repo/books"))
  assert books.BookPortion.from_id(id="5a3dfa6f751d5d9780b4c6ca", db_interface=db_fixture) is not None

  export_dir = os.path.join(os.path.dirname(tests.db.__file__), "textract-example-repo/books_v2")
  import shutil
  shutil.rmtree(path=export_dir, ignore_errors=True)
  db_fixture.dump_books(export_dir=export_dir)
  assert len(list(os.scandir(export_dir))) > 0


# We deliberately don't use find_one_and_update below - as a test.
def test_BookPortion_db_roundrip(db_fixture):
  book_portion = books.BookPortion.from_details(
    title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha",
    targets=[books.BookPositionTarget.from_details(container_id="xyz")])

  book_portions = db_fixture

  result = book_portions.update_doc(book_portion.to_json_map())
  logging.debug("update result is " + str(result))

  book_portion_retrieved = books.BookPortion.from_id(id=result["_id"], db_interface=book_portions)
  logging.info(book_portion_retrieved.__class__)
  logging.info(str(book_portion_retrieved.to_json_map()))
  logging.info(book_portion.to_json_map())
  assert(book_portion.equals_ignore_id(book_portion_retrieved))


def test_ImageAnnotation_db_roundrip(db_fixture):
  db = db_fixture
  book_portion = books.BookPortion.from_details(
    title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha")
  updated_book = book_portion.update_collection(db)
  target_page_id = updated_book._id
  annotation = ullekhanam.ImageAnnotation.from_details(targets=[
    ullekhanam.ImageTarget.from_details(container_id=str(target_page_id),
                                        rectangle=ullekhanam.Rectangle.from_details())],
    source=ullekhanam.DataSource.from_details("system_inferred", "xyz.py"))

  logging.debug(annotation.to_json_map())

  updated_annotation = annotation.update_collection(db_interface=db)
  logging.debug("update result is " + str(updated_annotation))
  assert(updated_annotation.equals_ignore_id(annotation))


def test_full_sentence_storage(db_fixture):
  # Add text annotation
  db = db_fixture

  book_portion = books.BookPortion.from_details(
    title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha")
  book_portion = book_portion.update_collection(db)

  target_image_id = book_portion._id
  text_annotation = ullekhanam.TextAnnotation.from_details(targets=[
    common.Target.from_details(container_id=book_portion._id)],
    source=ullekhanam.DataSource.from_details("system_inferred", "xyz.py"),
    content=common.Text.from_text_string(text_string=u"रामो विग्रवान् धर्मः।"))
  logging.debug(text_annotation.to_json_map())

  text_annotation = text_annotation.update_collection(db)
  logging.debug(text_annotation.to_json_map())

  samsAdhanI_source = ullekhanam.DataSource.from_details("system_inferred", "samsAdhanI/xyz.py")

  # Add pada db
  pada_annotation_rAmaH = SubantaAnnotation.from_details(targets=[
    ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
    source=samsAdhanI_source, word=common.Text.from_text_string(text_string=u"रामः"), root=common.Text.from_text_string(text_string=u"राम"),
    linga=u"pum", vibhakti="1", vachana=1)
  pada_annotation_rAmaH = pada_annotation_rAmaH.update_collection(db)
  logging.debug(pada_annotation_rAmaH.to_json_map())
  #
  # pada_annotation_vigrahavAn = ullekhanam.SubantaAnnotation.from_details(targets=[
  #   ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
  #   source=samsAdhanI_source, word=u"विग्रहवान्", root=u"विग्रहवत्",
  #   linga=u"pum", vibhakti="1", vachana=1)
  # pada_annotation_vigrahavAn = pada_annotation_vigrahavAn.update_collection(db)
  # logging.debug(pada_annotation_vigrahavAn.to_json_map())
  #
  # pada_annotation_avigrahavAn = ullekhanam.SubantaAnnotation.from_details(targets=[
  #   ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
  #   source=samsAdhanI_source, word=u"अविग्रहवान्", root=u"अविग्रहवत्",
  #   linga=u"pum", vibhakti="1", vachana=1)
  # pada_annotation_avigrahavAn = pada_annotation_avigrahavAn.update_collection(db)
  # logging.debug(pada_annotation_avigrahavAn.to_json_map())
  #
  # pada_annotation_dharmaH = ullekhanam.SubantaAnnotation.from_details(targets=[
  #   ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
  #   source=samsAdhanI_source, word=u"धर्मः", root=u"धर्म",
  #   linga=u"pum", vibhakti="1", vachana=1)
  # pada_annotation_dharmaH = pada_annotation_dharmaH.update_collection(db)
  # logging.debug(pada_annotation_dharmaH.to_json_map())
  #
  # pada_annotation_na = ullekhanam.SubantaAnnotation.from_details(targets=[
  #   ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
  #   source=samsAdhanI_source, word=u"न", root=u"न",
  #   linga=u"pum", vibhakti="1", vachana=1)
  # pada_annotation_na = pada_annotation_na.update_collection(db)
  # logging.debug(pada_annotation_na.to_json_map())
  #
  # sandhi_annotation_rAmovigrahavAn = ullekhanam.SandhiAnnotation.from_details(targets=
  # ullekhanam.TextTarget.from_containers(
  #   containers=[
  #     pada_annotation_rAmaH,
  #     pada_annotation_vigrahavAn]),
  #   source=samsAdhanI_source,
  #   combined_string=Text.from_text_string(text_string=u"रामो विग्रहवान्"))
  # sandhi_annotation_rAmovigrahavAn = sandhi_annotation_rAmovigrahavAn.update_collection(db)
  # logging.debug(sandhi_annotation_rAmovigrahavAn.to_json_map())
  #
  # sandhi_annotation_rAmoavigrahavAn = ullekhanam.SandhiAnnotation.from_details(targets=
  # ullekhanam.TextTarget.from_containers(
  #   containers=[
  #     pada_annotation_rAmaH,
  #     pada_annotation_avigrahavAn]),
  #   source=samsAdhanI_source,
  #   combined_string=Text.from_text_string(text_string=u"रामो विग्रहवान्"))
  # logging.debug(sandhi_annotation_rAmoavigrahavAn.to_json_map())


def test_JsonObjectNode_write(db_fixture):
  def add_book():
    from sanskrit_data.schema.books import BookPortion, BookPositionTarget
    db = db_fixture
    book_portion = BookPortion.from_details(
      title="something", path="myrepo/something", portion_class="book")
    book_portion = book_portion.update_collection(db)

    book_portion_1 = BookPortion.from_details(
      title="something_pg1", targets=[BookPositionTarget.from_details(container_id=book_portion._id)])
    book_portion_1.update_collection(db)

    book_portion_2 = BookPortion.from_details(
      title="something_pg2", targets=[BookPositionTarget.from_details(container_id=book_portion._id)])
    book_portion_2.update_collection(db)

  add_book()
  book = common.JsonObject.make_from_dict(db_fixture.find_one(find_filter={"path": "myrepo/something"}))
  logging.debug(str(book))
  json_node = common.JsonObjectNode.from_details(content=book)
  json_node.fill_descendents(db_interface=db_fixture)
  logging.debug(str(json_node))
  assert(json_node.children.__len__() == 2)