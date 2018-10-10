# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with
# the License. A copy of the License is located at
#     http://aws.amazon.com/apache2.0/
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import json
import boto3
import os

ecs_client = boto3.client('ecs')

ALB_NAME = 'ecs-demo-php-simple-app'
ECS_CLUSTER_NAME = 'ecs-bg-DeploymentPipeline-YM8402EZ4FKO-ecs-cluster'
REPO_URI = '697505841960.dkr.ecr.us-east-1.amazonaws.com/ecs-b-repos-15b3rkey5rakv'
FAMILY = 'simple-app'

def get_beta_service(elbname=ALB_NAME,
                     ecs_cluster_name=ECS_CLUSTER_NAME
                     ):
    """Discovers the live target group and non-production target group and swaps

            Args:
                elbname : name of the load balancer, which has the target groups to swap

            Raises:
                Exception: Any exception thrown by handler

    """
    elbclient = boto3.client('elbv2')

    try:

        elbresponse = elbclient.describe_load_balancers(Names=[elbname])
    except Exception as e:
        print("Load balancer not found. Reason: {0}".format(str(e)))
        return None

    listners = elbclient.describe_listeners(LoadBalancerArn=elbresponse['LoadBalancers'][0]['LoadBalancerArn'])

    for x in listners['Listeners']:
        if x['Port'] == 8080:
            beta_listenerarn = x['ListenerArn']
            break

    rules_response = elbclient.describe_rules(ListenerArn=beta_listenerarn)

    for x in rules_response['Rules']:
        if x['Priority'] == '1':
            betatargetgroup = x['Actions'][0]['TargetGroupArn']
            break

    ecs_service_arns = ecs_client.list_services(cluster=ecs_cluster_name)
    ecs_services = [srv.split("/")[1] for srv in ecs_service_arns['serviceArns']]
    ecs_service_details = ecs_client.describe_services(cluster=ecs_cluster_name,services=ecs_services)

    for service in ecs_service_details['services']:
        if 'loadBalancers' in service:
            print(service)
            albs = service['loadBalancers']
            for alb in albs:
                if 'targetGroupArn' in alb and \
                        alb['targetGroupArn'] == betatargetgroup:
                    beta_service = service['serviceName']
                    break

    print("Beta target group={0}".format(betatargetgroup))
    print("Beta service={0}".format(beta_service))
    return beta_service


def update_task_definition():
    with open('./simple-app-task-def.json', 'r') as data_file:
        task_def_org = json.load(data_file)
        for container in task_def_org['containerDefinitions']:
            if container['name'] == FAMILY:
                container['image'] = REPO_URI+':'+os.getenv('BUILD_NUMBER')
                print ('New image:{}'.format(container['image']))
                break

    task_definition = ecs_client.register_task_definition(**task_def_org)
    task_definition_arn = task_definition['taskDefinition']['taskDefinitionArn']
    print ('Task definition registered: {}'.format(task_definition_arn))
    return task_definition_arn


def update_service(service, new_task_definition_arn, ecs_cluster_name=ECS_CLUSTER_NAME):
    response = ecs_client.update_service(cluster=ecs_cluster_name,
                                         service=service,
                                         taskDefinition=new_task_definition_arn)
    print("Beta service {0} updated with task definition {1}".format(service, new_task_definition_arn))


if __name__ == "__main__":
    new_task_definition_arn = update_task_definition()
    service = get_beta_service()
    if service:
        update_service(service, new_task_definition_arn)