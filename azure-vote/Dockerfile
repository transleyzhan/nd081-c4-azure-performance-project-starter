# Pull the base image with Python 3.13
FROM python:3.13-slim

# Install necessary packages
RUN apt-get update && apt-get install -y \
    nginx \
    uwsgi \
    && apt-get clean

# Install Python dependencies
RUN pip install redis \
    opencensus \
    opencensus-ext-azure \
    opencensus-ext-flask \
    flask

# Copy the content of the current directory to the /app of the container
ADD . /app

# Set the working directory to /app
WORKDIR /app

# Copy nginx configuration file and set up uWSGI configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY uwsgi.ini /app/uwsgi.ini

# Start the services
CMD service nginx start && uwsgi --ini /app/uwsgi.ini
