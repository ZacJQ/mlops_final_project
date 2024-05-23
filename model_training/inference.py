import mlflow
import mlflow.sklearn
import pandas as pd

# Load the model
model_uri = "runs:/cd7a50347e3841b9840b528f55318868/model"  # Replace <RUN_ID> with the actual run ID from the MLflow UI
model = mlflow.sklearn.load_model(model_uri)

def preprocess_new_data(df):
    # Extract item quantities and convert to separate columns
    item_quantities = df['item_no_quantity'].str.extractall(r'(\d+)-(\d+)').unstack().fillna(0).astype(int)
    item_quantities.columns = [f'item_{i//2+1}_code' if i % 2 == 0 else f'item_{i//2+1}_quantity' for i in range(item_quantities.shape[1])]
    
    df = df.drop('item_no_quantity', axis=1).join(item_quantities)
    
    # Convert 'Veg_True' from Boolean to int
    df['Veg_True'] = df['Veg_True'].astype(int)

    # Select the same feature columns used in training
    feature_columns = [col for col in df.columns if col.startswith('item_') or col in ['no_of_chefs', 'Veg_True']]
    X = df[feature_columns]

    return X

# Example of loading new data from a CSV file
new_data_csv_path = 'model_training/test_1.csv'
new_df = pd.read_csv(new_data_csv_path)

# Preprocess the new data
X_new = preprocess_new_data(new_df)

# Make predictions
predictions = model.predict(X_new)
print(predictions)
