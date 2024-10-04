import pandas as pd
import json

# Function to calculate eGFR using the CKD-EPI Creatinine Equation (2021)
def calculate_egfr(row):
    age = row['age']
    sex = row['sex'].lower()
    scr = row['Serum_Creatinine']
    
    if sex == 'male':
        k = 0.9
        a = -0.302
        female_factor = 1
    else:
        k = 0.7
        a = -0.241
        female_factor = 1.012
    
    low = min(scr / k, 1)
    high = max(scr / k, 1)
    c = 142
    
    egfr = c * (low ** a) * (high ** -1.200) * (0.9938 ** age) * female_factor
    return egfr

# Load the patient demographics CSV into a DataFrame
def load_demographics(demographics_file):
    df_demographics = pd.read_csv(demographics_file)
    
    # Combine first_name and last_name into a full name
    df_demographics['Patient_Name'] = df_demographics['first_name'] + ' ' + df_demographics['last_name']
    
    # Keep only necessary columns
    df_demographics = df_demographics[['patient_id', 'Patient_Name', 'mobile_number', 'age', 'sex']]
    
    print(f"Demographics loaded: {len(df_demographics)} patients")
    return df_demographics

# Load the CMP data from JSON into a DataFrame
def load_cmp_data(cmp_file):
    with open(cmp_file) as jsonfile:
        cmp_data = json.load(jsonfile)
    
    filtered_data = []
    for patient_id, labs in cmp_data.items():
        # Look for the "Creatinine" measure in the patient's lab data
        creatinine_data = next((item for item in labs if item['measure'] == 'Creatinine'), None)
        if creatinine_data:
            filtered_data.append({
                'Patient_ID': patient_id,
                'Serum_Creatinine': creatinine_data['patient_measure']
            })
    
    cmp_df = pd.DataFrame(filtered_data)
    print(f"CMP data loaded: {len(cmp_df)} patients with serum creatinine data")
    return cmp_df

# Main function to process data and identify patients with CKD
# Main function to process data and identify patients with CKD
def screen_patients_for_ckd(demographics_file, cmp_file, output_file):
    df_demographics = load_demographics(demographics_file)
    df_cmp = load_cmp_data(cmp_file)
    
    # Convert both columns to string for consistent merging
    df_demographics['patient_id'] = df_demographics['patient_id'].astype(str)
    df_cmp['Patient_ID'] = df_cmp['Patient_ID'].astype(str)
    
    # Merge the two DataFrames on Patient_ID
    df_merged = pd.merge(df_demographics, df_cmp, left_on='patient_id', right_on='Patient_ID')
    print(f"Data merged: {len(df_merged)} patients with complete records")
    
    # Calculate eGFR for each patient
    df_merged['eGFR'] = df_merged.apply(calculate_egfr, axis=1)
    
    # Filter patients with eGFR <= 65
    df_screened = df_merged[df_merged['eGFR'] <= 65]
    
    # Select the required columns for the output
    df_output = df_screened[['patient_id', 'Patient_Name', 'mobile_number', 'eGFR']]
    df_output.columns = ['Patient_ID', 'Patient_Name', 'Patient_Phone', 'Patient_eGFR']
    
    # Write the output to a CSV file
    df_output.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")


# Execute the script with provided file paths
if __name__ == "__main__":
    demographics_file = 'patient_demographics.csv'
    cmp_file = 'cmp.json'
    output_file = 'results.csv'
    
    screen_patients_for_ckd(demographics_file, cmp_file, output_file)
