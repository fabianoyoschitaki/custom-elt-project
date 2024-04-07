FROM python:3.8-slim

RUN apt-get update && apt-get install -y postgresql-client

# copy the contents of the ELT so that the container has access to it
COPY elt_script.py .

CMD ["python", "elt_script.py"]