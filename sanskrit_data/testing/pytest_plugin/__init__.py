from sanskrit_data.schema import common


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, common.JsonObject) and isinstance(right, common.JsonObject) and op == "==":
        return [
            "{} != {}".format(str(left), str(right)),
        ]