from budget.templatetags import budget_extras

def test_mul_filter():
    assert budget_extras.mul(2, 3) == 6

def test_div_filter():
    assert budget_extras.div(10, 2) == 5
