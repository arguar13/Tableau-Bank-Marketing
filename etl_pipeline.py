import os
import urllib.request
import zipfile
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_and_extract_data(base_dir):
    """Download the UCI Bank Marketing (additional) archive into `base_dir` and unzip it."""
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00222/bank-additional.zip"
    zip_path = os.path.join(base_dir, "bank_raw_data.zip")
    
    logging.info(f"Starting download of dataset from: {url}")
    try:
        urllib.request.urlretrieve(url, zip_path)
        logging.info("Download completed successfully.")
    except Exception as e:
        logging.error(f"Error downloading the file: {e}")
        raise

    logging.info("Extracting files...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(base_dir)
    logging.info("Extraction completed.")

def process_data(base_dir):
    """Load the full campaign file and add the fields the Tableau dashboard uses."""
    raw_csv_path = os.path.join(base_dir, "bank-additional", "bank-additional-full.csv")
    logging.info("Loading the original (raw) dataset...")

    df = pd.read_csv(raw_csv_path, sep=';')
    logging.info(f"Dataset loaded. Original dimensions: {df.shape}")

    logging.info("Applying transformations and feature engineering...")

    # 1. 0/1 target, so the conversion rate is AVG([conversion_flag]) in Tableau
    df['conversion_flag'] = df['y'].apply(lambda x: 1 if x == 'yes' else 0)
    
    # 2. Age Bins for demographic segmentation
    bins = [0, 25, 35, 45, 55, 65, 120]
    labels = ['17-25', '26-35', '36-45', '46-55', '56-65', '66+']  # the youngest client is 17
    df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels, right=True)
    
    # 3. Standardize 'unknown' values and capitalization for a cleaner display
    cols_with_unknown = ['job', 'marital', 'education', 'default', 'housing', 'loan']
    for col in cols_with_unknown:
        df[col] = df[col].replace('unknown', 'Unknown')
        df[col] = df[col].str.capitalize()
    
    # 4. '03-Mar' sorts chronologically even as text (the campaigns have no Jan/Feb calls)
    month_map = {
        'mar': '03-Mar', 'apr': '04-Apr', 'may': '05-May', 'jun': '06-Jun',
        'jul': '07-Jul', 'aug': '08-Aug', 'sep': '09-Sep', 'oct': '10-Oct',
        'nov': '11-Nov', 'dec': '12-Dec'
    }
    df['month_mapped'] = df['month'].map(month_map)
    
    # 5. Convert durations from seconds to minutes for better interpretability.
    #    Call duration is only known after the call ends, so it describes engagement,
    #    not a lever for choosing whom to call: the dashboard uses contact attempts instead.
    df['duration_minutes'] = round(df['duration'] / 60, 2)
    
    logging.info("Transformations completed.")
    return df

def save_processed_data(df, base_dir):
    """Write the Tableau extract next to the script."""
    final_path = os.path.join(base_dir, "end_bank_marketing_for_tableau.csv")
    
    logging.info(f"Saving processed dataset to: {final_path}")
    # Comma-separated, unlike the ';' source file
    df.to_csv(final_path, index=False, encoding='utf-8')
    logging.info("ETL process completed successfully. The dataset is ready for Tableau.")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Working directory: {script_dir}")
    
    download_and_extract_data(script_dir)
    processed_df = process_data(script_dir)
    save_processed_data(processed_df, script_dir)

if __name__ == "__main__":
    main()