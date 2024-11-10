# pull official base image
FROM python:3.10-slim

# set work directory
WORKDIR /src

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY requirements.txt /src/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . /src/

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
