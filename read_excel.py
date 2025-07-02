import pandas as pd

def read_excel_file(file_path):
    try:
        # Read the Excel file
        excel_data = pd.read_excel(file_path, sheet_name=None)
        
        # Display sheet names
        print(f"Excel file contains the following sheets: {list(excel_data.keys())}")
        
        # Display the structure of each sheet
        for sheet_name, df in excel_data.items():
            print(f"\n\nSheet: {sheet_name}")
            print(f"Shape: {df.shape} (rows, columns)")
            print("Columns:", list(df.columns))
            print("\nSample data (first 5 rows):")
            print(df.head(5))
    
    except Exception as e:
        print(f"Error reading Excel file: {e}")

# Path to the Excel file
file_path = "Basketball Sources Links.xlsx"

# Read and display the Excel file
read_excel_file(file_path) 