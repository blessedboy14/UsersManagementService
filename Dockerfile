FROM python:3.10.12

RUN mkdir /backend
WORKDIR /backend

RUN apt update

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

CMD [ "python3", "-m", "uvicorn", "src.main:app", "--reload" ]