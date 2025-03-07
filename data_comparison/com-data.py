import pandas as pd
import os

file_path = 'input.csv'

# Check if the file exists and print an appropriate message
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
else:
    try:
        # Load the data from the CSV file
        df = pd.read_csv(file_path)
        
        # Print the column names to verify them
        print("Column names in the CSV file:", df.columns)
        
        # Function to compare dates and return the difference if any
        def compare_dates(row):
            date1 = str(row['A']).strip().lower()
            date2 = str(row['B']).strip().lower()
            date3 = str(row['D']).strip().lower()
            date4 = str(row['E']).strip().lower()
            
            if date1 == date3 and date2 == date4:
                return ''
            else:
                return 'Mismatch'
        
        # Validate column names before applying the comparison function
        required_columns = ['A', 'B', 'D', 'E']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"The following columns are missing in the CSV file: {', '.join(missing_columns)}")
        else:
            # Apply the function to each row and store the result in column C
            df['C'] = df.apply(compare_dates, axis=1)
            
            # Save the updated DataFrame back to a CSV file
            output_file_path = 'output_file.csv'
            df.to_csv(output_file_path, index=False)
            
            print(f"Output saved to {output_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
