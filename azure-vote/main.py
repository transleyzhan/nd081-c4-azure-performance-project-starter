from flask import Flask, request, render_template
import os
import random
import redis
import socket
import sys
import logging
from datetime import datetime

# App Insights
# Import required libraries for App Insights
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.log_exporter import AzureEventHandler, AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.trace import config_integration
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

# Metrics
stats = stats_module.stats
view_manager = stats.view_manager

config_integration.trace_integrations(["logging"])
config_integration.trace_integrations(["requests"])

# Logging
logger = logging.getLogger(__name__) 
# Setup logger
handler = AzureLogHandler(
    connection_string="InstrumentationKey=efea2165-d59a-4e01-9c55-1039f18e6871;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=97124d87-12d2-4582-ba0a-8daec3daca40"
)

# Metrics
handler.setFormatter(logging.Formatter("TraceId: %(traceId)s, SpanId: %(spanId)s, Message: %(message)s"))
# Setup exporter
logger.addHandler(handler)
logger.addHandler(
    AzureEventHandler(
        connection_string="InstrumentationKey=efea2165-d59a-4e01-9c55-1039f18e6871;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=97124d87-12d2-4582-ba0a-8daec3daca40"
    )
)

logger.setLevel(logging.INFO)

exporter = metrics_exporter.new_metrics_exporter(
    enable_standard_metrics=True,
    connection_string="InstrumentationKey=efea2165-d59a-4e01-9c55-1039f18e6871;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=97124d87-12d2-4582-ba0a-8daec3daca40",
) # Setup exporter

view_manager.register_exporter(exporter)

# Tracing
tracer = Tracer(
    exporter=AzureExporter(
        connection_string="InstrumentationKey=efea2165-d59a-4e01-9c55-1039f18e6871;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=97124d87-12d2-4582-ba0a-8daec3daca40"
    ),
    sampler=ProbabilitySampler(1.0),
) 
# Setup tracer

app = Flask(__name__)

# Requests
middleware = FlaskMiddleware(
    app,
    exporter=AzureExporter(
        connection_string="InstrumentationKey=efea2165-d59a-4e01-9c55-1039f18e6871;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=97124d87-12d2-4582-ba0a-8daec3daca40"
    ),
    sampler=ProbabilitySampler(rate=1.0),
) 
# Setup flask middleware

# Load configurations from environment or config file
app.config.from_pyfile('config_file.cfg')

if ("VOTE1VALUE" in os.environ and os.environ['VOTE1VALUE']):
    button1 = os.environ['VOTE1VALUE']
else:
    button1 = app.config['VOTE1VALUE']

if ("VOTE2VALUE" in os.environ and os.environ['VOTE2VALUE']):
    button2 = os.environ['VOTE2VALUE']
else:
    button2 = app.config['VOTE2VALUE']

if ("TITLE" in os.environ and os.environ['TITLE']):
    title = os.environ['TITLE']
else:
    title = app.config['TITLE']

# Comment/remove the next two lines of code.
# Redis Connection to a local server running on the same machine where the current FLask app is running. 
# r = redis.Redis()
# Redis configurations
redis_server = os.environ['REDIS']

# Redis Connection to another container
try:
    if "REDIS_PWD" in os.environ:
        r = redis.StrictRedis(host=redis_server,
                           port=6379,
                           password=os.environ['REDIS_PWD'])
    else:
        r = redis.Redis(redis_server)
        r.ping()
except redis.ConnectionError:
      exit('Failed to connect to Redis, terminating.')

# Change title to host name to demo NLB
if app.config['SHOWHOST'] == "true":
    title = socket.gethostname()

# Init Redis
if not r.get(button1): r.set(button1,0)
if not r.get(button2): r.set(button2,0)

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'GET':

        # Get current values
        vote1 = r.get(button1).decode('utf-8')
        # use tracer object to trace cat vote
        logger.info("Request GET: Cats Vote")
        with tracer.span(name="Cats Vote") as span:
            print("Cats Vote")
            
        vote2 = r.get(button2).decode('utf-8')
        # use tracer object to trace dog vote
        logger.info("Request GET: Dogs Vote")
        with tracer.span(name="Dogs Vote") as span:
            print("Dogs Vote")

        # Return index with values
        return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

    elif request.method == 'POST':

        if request.form['vote'] == 'reset':

            # Empty table and return results
            r.set(button1,0)
            r.set(button2,0)
            vote1 = r.get(button1).decode('utf-8')
            properties = {'custom_dimensions': {'Cats Vote': vote1}}
            # use logger object to log cat vote
            logger.info("Request POST: Cats Vote, reset")
            logger.info("Cats Vote", extra=properties)

            vote2 = r.get(button2).decode('utf-8')
            properties = {'custom_dimensions': {'Dogs Vote': vote2}}
            # use logger object to log dog vote
            logger.info("Request POST: Dogs Vote, reset")
            logger.info("Dogs Vote", extra=properties)

            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

        else:
            # use logger to insert vote result into DB
            logger.info("Request POST: Insert vote result into DB")

            # Insert vote result into DB
            vote = request.form['vote']
            r.incr(vote,1)

            # Get current values
            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')

            # Return results
            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

if __name__ == "__main__":
    # Use the statement below when running locally
    #app.run() 
    # Use the statement below before deployment to VMSS
    app.run(host='0.0.0.0', threaded=True, debug=True) # remote
