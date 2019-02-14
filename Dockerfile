FROM debian:stretch
RUN apt-get update && apt-get install -y python3-django python3-requests
RUN mkdir /django-apps
WORKDIR /django-apps
ADD ./src /django-apps/
EXPOSE 8000
CMD ["python3", "manage.py", "runserver", "0:8000"]
