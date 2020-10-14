import logging
import os
import traceback

from sanskrit_data import collection_helper
from sanskrit_data.schema.common import JsonObject


def json_compare(actual_object, expected_content_path):
    if not os.path.exists(expected_content_path):
        logging.warning("File must have been deliberately deleted as obsolete. So, will dump a new file for future tests.")
        actual_object.dump_to_file(filename=expected_content_path,
                                floating_point_precision=4)
        return 

    expected = JsonObject.read_from_file(filename=expected_content_path)
    try:
        # The below would be actually slower (1min+), and leads to bug output dump in case of failure.
        # assert str_actual == str_expected 
        # The below is better, but still slower (35s and leads to bug output dump in case of failure.
        # assert actual == expected

        # The below is faster - 20s and produces concise difference.
        collection_helper.assert_approx_equals(x=actual_object, y=expected, floating_point_precision=4)
    except:
        # firefox does not identify files not ending with .json as json. Hence not naming .json.local.
        actual_content_path = expected_content_path.replace(".json", "_actual.local.json")
        actual_object.dump_to_file(filename=actual_content_path, floating_point_precision=4)
        traceback.print_exc()
        raise
