import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import mlflow
import mlflow.sklearn
import os

def preprocess_data(df):
    item_quantities = df['item_no_quantity'].str.extractall(r'(\d+)-(\d+)').unstack().fillna(0).astype(int)
    item_quantities.columns = [f'item_{i//2+1}_code' if i % 2 == 0 else f'item_{i//2+1}_quantity' for i in range(item_quantities.shape[1])]
    
    df = df.drop('item_no_quantity', axis=1).join(item_quantities)
    df['Veg_True'] = df['Veg_True'].astype(int)
    X = df.drop('time_to_prep', axis=1)
    y = df['time_to_prep']
    return X, y, df

def train_model(df):
    X, y, df_preprocessed = preprocess_data(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    return model, mse, df_preprocessed

def mlflow_train_and_log(df, experiment_name='FoodPrepTimePrediction'):
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run() as run:
        model, mse, df_preprocessed = train_model(df)
        mlflow.sklearn.log_model(model, "model")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_metric("mse", mse)
        training_data_path = "training_data.csv"
        df_preprocessed.to_csv(training_data_path, index=False)
        mlflow.log_artifact(training_data_path)
        os.remove(training_data_path)
        print(f"Model logged with MSE: {mse}")
        print(f"Run ID: {run.info.run_id}")
        return model, run.info.run_id

# Load training data
csv_path = '/Users/zac/Codes/ML_Ops/ML_Ops_Project/Final_project/model_training/Train_1.csv'
df = pd.read_csv(csv_path)

# Train and log the model with MLflow
model, run_id = mlflow_train_and_log(df)

print(f"Run ID for this run is: {run_id}")
