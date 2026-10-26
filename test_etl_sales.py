import pandas as pd
from etl_sales import transform_sales


def test_product_code_cleaning():
    # 1. ARRANGE: Create test data with unformatted product code
    dirty_data = pd.DataFrame({
        'invoice_date': ['15-05-2026'],
        'quantity': ['5'],
        'total_value': ['100.50'],
        'product_code': [' a b c '],  # Lowercase letters with surrounding whitespace
        'customer': ['Hospital A']
    })

    # 2. ACT: Process dirty data through the transformation function
    result = transform_sales(dirty_data)

    # 3. ASSERT: Verify that the product code was properly cleaned and uppercased
    cleaned_code = result['product_code'].iloc[0]
    assert cleaned_code == 'ABC'


def test_null_handling_and_dates():
    # 1. ARRANGE: Create test data with an invalid date and null customer
    dirty_data = pd.DataFrame({
        'invoice_date': ['invalid_text'],
        'quantity': ['2'],
        'total_value': ['50.0'],
        'product_code': ['PROD1'],
        'customer': [None]  # Null customer should become 'Unknown'
    })

    # 2. ACT: Process dirty data through the transformation function
    result = transform_sales(dirty_data)

    # 3. ASSERT: Verify cleaning rules for null values and invalid dates
    # Customer field should be replaced with 'Unknown'
    assert result['customer'].iloc[0] == 'Unknown'
    
    # Invalid date string should be coerced to NaT (Not a Time)
    assert pd.isna(result['invoice_date'].iloc[0])
