FROM python:3.11-alpine

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /code

CMD ["python3", "main.py"]
