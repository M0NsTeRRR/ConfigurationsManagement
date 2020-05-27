FROM python:3.8-alpine

LABEL maintainer="Ludovic Ortega mastership@hotmail.fr"

# update package
RUN apk update

# copy program and requirements
COPY . /app/ConfigurationsManagement

# set workdir
WORKDIR /app/ConfigurationsManagement/

# install dependencies
RUN pip install -e .[production]

# set environment variables
ENV FLASK_APP "website"
ENV FLASK_ENV "production"

# compile translations
RUN pybabel compile -d website/translations

# expose gunicorn binded port
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "website.wsgi:app", "--bind", "0.0.0.0:8000"]