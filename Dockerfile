FROM python:3.10.12-alpine3.18 as requirements-stage

RUN mkdir /backend
WORKDIR /backend

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /backend/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.10.12-alpine3.18

WORKDIR /code

COPY --from=requirements-stage /backend/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/src

CMD [ "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080" ]