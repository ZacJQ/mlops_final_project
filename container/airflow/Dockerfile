FROM apache/airflow:2.1.4

USER root
RUN apt-get update && apt-get install -y gcc python3-dev

USER airflow
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY dags/ /opt/airflow/dags/

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["bash", "-c", "airflow db init && airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com && airflow scheduler & airflow webserver"]