import ml.category_model as cm


def test_predict_returns_string():
    result = cm.predict_category("TEST DESCRIPTION")
    assert isinstance(result, str)


def test_predict_is_stable_on_multiple_calls():
    # calling multiple times should not raise and should return a string
    r1 = cm.predict_category("FOO BAR")
    r2 = cm.predict_category("FOO BAR")
    assert isinstance(r1, str)
    assert isinstance(r2, str)
