import pandas as pd
from etl_vendas import transform_sales

def test_limpeza_do_codigo_do_produto():
    # 1. ARRANGE (Preparação): Criamos um mini-dataframe falso com um erro proposital
    dados_sujos = pd.DataFrame({
        'invoice_date': ['15-05-2026'],
        'quantity': ['5'],
        'total_value': ['100.50'],
        'product_code': [' a b c '],  # O erro está aqui: letras minúsculas e cheias de espaços
        'customer': ['Hospital A']
    })

    # 2. ACT (Ação): Passamos o nosso dado sujo pela sua função oficial
    resultado = transform_sales(dados_sujos)

    # 3. ASSERT (Verificação): O robô confere se o código fez o que devia
    # Pegamos o valor que saiu da limpeza
    codigo_limpo = resultado['product_code'].iloc[0]
    
    # O comando mágico 'assert' (garanta). 
    # Ele diz: "Se o código não for 'ABC', exploda um erro vermelho. Se for 'ABC', fique verde."
    assert codigo_limpo == 'ABC'


def test_tratamento_de_nulos_e_datas():
    # 1. ARRANGE: Criamos dados com data inválida e cliente nulo
    dados_sujos = pd.DataFrame({
        'invoice_date': ['texto_invalido'],
        'quantity': ['2'],
        'total_value': ['50.0'],
        'product_code': ['PROD1'],
        'customer': [None]  # O cliente nulo deve virar 'Unknown'
    })

    # 2. ACT
    resultado = transform_sales(dados_sujos)

    # 3. ASSERT: Verificamos se as regras de limpeza funcionaram
    # O cliente deve ter virado 'Unknown'
    assert resultado['customer'].iloc[0] == 'Unknown'
    
    # A data inválida deve ter virado NaT (Not a Time) via coerce
    assert pd.isna(resultado['invoice_date'].iloc[0])
