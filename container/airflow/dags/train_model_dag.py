from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import mlflow
import pandas as pd
import sqlalchemy
from sklearn.linear_model import LinearRegression
import joblib
from kafka import KafkaConsumer
import json


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

def consume_messages_from_kafka():
    consumer = KafkaConsumer(
        'order_topic',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='order-consumer-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    messages = []
    for message in consumer:
        messages.append(message.value)
        if len(messages) >= 100:  # Process every 100 messages for example
            break

    # Save messages to a CSV for training
    df = pd.DataFrame(messages)
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
consume_messages_task = PythonOperator(
    task_id='consume_messages_from_kafka',
    python_callable=consume_messages_from_kafka,
    dag=dag,
)

train_model_task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag,
)

# Set task dependencies
consume_messages_task >> train_model_task
