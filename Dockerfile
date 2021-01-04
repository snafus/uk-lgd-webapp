FROM python:3.8

LABEL MAINTAINER="James  Wa JW@x.x"

ENV GROUP_ID=1000 \
    USER_ID=1000


RUN echo "Build number"

WORKDIR /var/www/

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
RUN pip install gunicorn

RUN addgroup --gid $GROUP_ID www
RUN adduser --system --uid $USER_ID --gid $GROUP_ID --disabled-password --shell /bin/sh www
#RUN adduser --system  --disabled-password --shell /bin/sh --uid $USER_ID  www www

USER www

EXPOSE 5000

#ADD . /var/www/
#COPY . /var/www/
COPY wsgi.py /var/www 
COPY app.py /var/www
COPY templates /var/www
COPY static /var/www

COPY templates/* /var/www/templates/
COPY static/* /var/www/static/
#COPY static/* /var/www/static/

CMD [ "gunicorn", "-w", "4", "--bind", "0.0.0.0:5000", "wsgi"]

