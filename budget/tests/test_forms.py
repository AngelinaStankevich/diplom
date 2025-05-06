from budget.forms import CategoryForm

def test_category_form_valid():
    form = CategoryForm(data={"name": "Транспорт", "is_income": False, "color": "#123456"})
    assert form.is_valid()
