#!/usr/bin/env python3

import argparse
import os
import time
from pprint import pprint

import googleapiclient.discovery
import google.auth
import sys
sys.path.append('../')
#from cloud.parts import *

credentials, project = google.auth.default()
service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)
zone = "us-west1-b"
fwPort = 5000
fwName = 'allow-{}'.format(fwPort)
instanceName = 'blog'
nodeType = 'f1-micro'


if not project or project == '':
    print("No project found, or need to run 'gcloud config set project <project-name>'")

#
#
# Stub code - just lists all instances
#
def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None

print("Your running instances are:")
for instance in list_instances(service, project, 'us-west1-b'):
    print(instance['name'])

create_firewall_rule(service, project, fwPort, fwName)

try:
    operation = create_instance(service, project, zone, instanceName,
        nodeType = nodeType,
        scriptFile = 'startup-script.sh',
        fwName = fwName)
    wait_for_operation(service, project, zone, operation['name'])
except googleapiclient.errors.HttpError as exp:
    print("An instance may already be running")
    print(exp)

try:
    instanceResponse = service.instances().get(project=project, zone=zone, instance=instanceName).execute()
    if instanceResponse:
        instanceIP = instanceResponse['networkInterfaces'][0]['accessConfigs'][0]['natIP']
        print(f"The blog is runnin at http://{instanceIP}:{fwPort}")
except googleapiclient.errors.HttpError as exp:
    print(f"Unable to locate instance {instanceName} to get the IP address")
    print(exp)

