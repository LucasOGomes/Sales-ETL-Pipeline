import logging
import pandas as pd
import sqlite3
import yaml

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Carrega a configuração inicial para o Logger
config_temp = load_config()

logging.basicConfig(
    filename=config_temp["paths"]["log_file"], # Agora dinâmico através do YAML
    level=logging.INFO,
    format='%(asctime)s | %(name)s | Linha: %(lineno)d | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# 1. EXTRACT 
def load_sales(path: str) -> pd.DataFrame:
    try:
        logger.info(f"A iniciar extração do ficheiro: {path}")
        df = pd.read_csv(path, sep=';', encoding='latin-1', decimal=',', thousands='.')
        logger.info(f"Sucesso: {len(df)} linhas carregadas.")
        return df
    except FileNotFoundError:
        logger.error(f"Ficheiro não encontrado: {path}", exc_info=True)
        # Mas não podemos esquecer de matar o programa para não vazar um "None")
        raise

def calculate_monthly_avg(df: pd.DataFrame) -> pd.DataFrame:
    try:
        logger.info("A calcular o preço médio por mês...")
        
        # Agrupa pelo mês e calcula a média do valor total
        df_avg = df.groupby('month')['total_value'].mean().reset_index()
        df_avg['total_value'] = df_avg['total_value'].round(2)
        
        # O "print" do Engenheiro de Dados: 
        # Usamos o .to_string() para o logger formatar a tabela bonitinha no terminal
        logger.info(f"Média Mensal Calculada com Sucesso:\n{df_avg.to_string()}")
        
        return df_avg
        
    except Exception as e:
        logger.error("Erro ao calcular a média mensal.", exc_info=True)
        raise

# 2. TRANSFORM (Toda a limpeza das Tasks 1 a 5)
def transform_sales(df: pd.DataFrame) -> pd.DataFrame:
    try:
        logger.info("A iniciar transformações de dados...")

        # Cleaning and type conversion
        df['invoice_date'] = pd.to_datetime(df['invoice_date'], errors='coerce', format='%d-%m-%Y')
        df['quantity'] = df['quantity'].astype(int)
        df['total_value'] = df['total_value'].astype(float)
        df['product_code'] = df['product_code'].astype(str).str.replace(' ', '').str.upper()
        df = df.dropna(subset=['total_value'])
        df = df.drop_duplicates()
        
        # O astype(str) no final transforma o período "2026-10" num texto normal, que o SQLite aceita!
        df['month'] = df['invoice_date'].dt.to_period('M').astype(str)
        df['customer'] = df['customer'].fillna('Unknown')

        logger.info("Transformações concluídas.")
        return df
    
    except Exception as e:
        logger.error("Erro ao transformar dados.", exc_info=True)
        raise
    
# 3. LOAD (A lógicas de banco de dados da Task 6)
def load_to_database(df: pd.DataFrame, table_name: str = 'sales', db_name: str = ':memory:') -> None:
    logger.info(f"A criar a tabela '{table_name}' no banco '{db_name}'...")
    
    conn = sqlite3.connect(db_name)
    
    # Em vez de chumbar a palavra 'sales', passamos a variável table_name
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    conn.close()
    logger.info("Carregamento no banco concluído com sucesso.")

# 4. ORQUESTRADOR (O maestro que chama as funções na ordem certa)
def run_pipeline(config_path: str = "config.yaml") -> None:
    # Carrega as configurações para a execução do pipeline
    config = load_config(config_path)
    
    # Busca o caminho do CSV dentro do YAML
    caminho_do_arquivo = config["paths"]["raw_sales_csv"]
    
    # Executa o pipeline passo a passo
    df_raw = load_sales(caminho_do_arquivo)
    df_clean = transform_sales(df_raw)
    df_averages = calculate_monthly_avg(df_clean)
    
    # Passa as configurações de banco de dados diretamente do YAML
    load_to_database(
        df_clean, 
        table_name=config["database"]["tables"]["cleaned_sales"], 
        db_name=config["database"]["db_name"]
    )
    load_to_database(
        df_averages, 
        table_name=config["database"]["tables"]["monthly_avg"], 
        db_name=config["database"]["db_name"]
    )

    logger.info("Pipeline ETL finalizado com sucesso!")

if __name__ == "__main__":
    run_pipeline()