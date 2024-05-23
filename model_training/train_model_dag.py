from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import mlflow
import pandas as pd
import sqlalchemy
from sklearn.linear_model import LinearRegression
import joblib

# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Initialize the DAG
dag = DAG(
    'train_model_dag',
    default_args=default_args,
    description='A DAG to train the food preparation time model',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
)

def fetch_training_data():
    DATABASE_URL = "postgresql://postgres:1234@localhost/restaurant_db"
    engine = sqlalchemy.create_engine(DATABASE_URL)
    query = "SELECT * FROM training_data"
    df = pd.read_sql(query, engine)
    df.to_csv('/tmp/training_data.csv', index=False)

def train_model():
    # Load the data
    df = pd.read_csv('/tmp/training_data.csv')

    # Preprocess the data
    X = df[['item_no_quantity', 'no_of_chefs', 'Veg_True']]
    y = df['time_to_prep']

    # Convert categorical data
    X = pd.get_dummies(X, columns=['item_no_quantity', 'Veg_True'], drop_first=True)

    # Train the model
    model = LinearRegression()
    model.fit(X, y)

    # Save the model
    joblib.dump(model, '/tmp/model.pkl')

    # Log the model with MLflow
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("food_prep_time_prediction")
    with mlflow.start_run():
        mlflow.sklearn.log_model(model, "model")
        mlflow.log_artifact('/tmp/training_data.csv', "data")
        mlflow.log_artifact('/tmp/model.pkl', "model")

# Define the tasks
fetch_data_task = PythonOperator(
    task_id='fetch_training_data',
    python_callable=fetch_training_data,
    dag=dag,
)

train_model_task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag,
)

# Set task dependencies
fetch_data_task >> train_model_task
