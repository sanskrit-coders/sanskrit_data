import logging

import pytest

import tests
import tests.db
from sanskrit_data.schema import ullekhanam, common, books

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

@pytest.fixture(scope='module')
def db_fixture(request):
  return tests.db.ullekhanam_db_fixture(request=request)


def test_target_validation(db_fixture):
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


  book_portion_2 = books.BookPortion.from_details(
    title="halAyudhakoshaH1", authors=["halAyudhaH"], path="myrepo/halAyudha", targets=[books.BookPositionTarget.from_details(container_id=updated_annotation._id)])
  with pytest.raises(common.TargetValidationError) as exception_info:
    book_portion_2_updated = book_portion_2.update_collection(db_interface=db)
  assert "does not belong to" in exception_info.value.message
