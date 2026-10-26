import logging
import pandas as pd
import sqlite3
import yaml

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config_temp = load_config()

logging.basicConfig(
    filename=config_temp["paths"]["log_file"],
    level=logging.INFO,
    format='%(asctime)s | %(name)s | Linha: %(lineno)d | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# 1. EXTRACT 
def load_sales(path: str) -> pd.DataFrame:
    try:
        logger.info(f"Starting file extraction: {path}")
        df = pd.read_csv(path, sep=';', encoding='latin-1', decimal=',', thousands='.')
        logger.info(f"Success: {len(df)} rows loaded.")
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {path}", exc_info=True)
        raise

def calculate_monthly_avg(df: pd.DataFrame) -> pd.DataFrame:
    try:
        logger.info("Calculating the average price per month...")
        
        df_avg = df.groupby('month')['total_value'].mean().reset_index()
        df_avg['total_value'] = df_avg['total_value'].round(2)
        
        logger.info(f"Monthly Average Successfully Calculated:\n{df_avg.to_string()}")
        
        return df_avg
        
    except Exception as e:
        logger.error("Error calculating the monthly average.", exc_info=True)
        raise

# 2. TRANSFORM
def transform_sales(df: pd.DataFrame) -> pd.DataFrame:
    try:
        logger.info("Starting data transformations...")

        # Cleaning and type conversion
        df['invoice_date'] = pd.to_datetime(df['invoice_date'], errors='coerce', format='%d-%m-%Y')
        df['quantity'] = df['quantity'].astype(int)
        df['total_value'] = df['total_value'].astype(float)
        df['product_code'] = df['product_code'].astype(str).str.replace(' ', '').str.upper()
        df = df.dropna(subset=['total_value'])
        df = df.drop_duplicates()
        
        df['month'] = df['invoice_date'].dt.to_period('M').astype(str)
        df['customer'] = df['customer'].fillna('Unknown')

        logger.info("Transformations completed.")
        return df
    
    except Exception as e:
        logger.error("Error transforming data.", exc_info=True)
        raise
    
# 3. LOAD
def load_to_database(df: pd.DataFrame, table_name: str = 'sales', db_name: str = ':memory:') -> None:
    logger.info(f"Creating table '{table_name}' in database '{db_name}'...")
    
    conn = sqlite3.connect(db_name)
    
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    conn.close()
    logger.info("Loading into the database completed successfully.")

# 4. Workflow Orchestrator 
def run_pipeline(config_path: str = "config.yaml") -> None:
    config = load_config(config_path)
    
    caminho_do_arquivo = config["paths"]["raw_sales_csv"]
    
    df_raw = load_sales(caminho_do_arquivo)
    df_clean = transform_sales(df_raw)
    df_averages = calculate_monthly_avg(df_clean)
    
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
