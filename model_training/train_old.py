import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import mlflow
import mlflow.sklearn
import os

# Data preprocessing function
def preprocess_data(df):
    # Extract item quantities and convert to separate columns
    item_quantities = df['item_no_quantity'].str.extractall(r'(\d+)-(\d+)').unstack().fillna(0).astype(int)
    item_quantities.columns = [f'item_{i//2+1}_code' if i % 2 == 0 else f'item_{i//2+1}_quantity' for i in range(item_quantities.shape[1])]
    
    df = df.drop('item_no_quantity', axis=1).join(item_quantities)

    # Convert 'Veg_True' from Boolean to int
    df['Veg_True'] = df['Veg_True'].astype(int)

    # Split into features and target variable
    X = df.drop('time_to_prep', axis=1)
    y = df['time_to_prep']

    return X, y, df

# Training function
def train_model(df):
    X, y, df_preprocessed = preprocess_data(df)
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize and train the model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Predict and evaluate the model
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    
    return model, mse, df_preprocessed

# MLflow training and logging function
def mlflow_train_and_log(df, experiment_name='FoodPrepTimePrediction'):
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run():
        model, mse, df_preprocessed = train_model(df)
        
        # Log the model
        mlflow.sklearn.log_model(model, "model")
        
        # Log parameters and metrics
        mlflow.log_param("n_estimators", 100)
        mlflow.log_metric("mse", mse)
        
        # Save preprocessed training data
        training_data_path = "training_data.csv"
        df_preprocessed.to_csv(training_data_path, index=False)
        mlflow.log_artifact(training_data_path)
        
        # Clean up the CSV file
        os.remove(training_data_path)
        
        print(f"Model logged with MSE: {mse}")
        
        return model

# Example of loading data from a CSV file
csv_path = '/Users/zac/Codes/ML_Ops/ML_Ops_Project/Final_project/model_training/Book1.csv'
df = pd.read_csv(csv_path)

# Train and log the model with MLflow
model = mlflow_train_and_log(df)
