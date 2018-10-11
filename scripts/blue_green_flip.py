from __future__ import print_function

import json
import boto3
import sys
import traceback

elbclient = boto3.client('elbv2')
ALB_NAME = 'ecs-demo-php-simple-app'

def swaptargetgroups(elbname):
    """Discovers the live target group and non-production target group and swaps

            Args:
                elbname : name of the load balancer, which has the target groups to swap

            Raises:
                Exception: Any exception thrown by handler

    """
    elbresponse = elbclient.describe_load_balancers(Names=[elbname])

    listners = elbclient.describe_listeners(LoadBalancerArn=elbresponse['LoadBalancers'][0]['LoadBalancerArn'])
    for x in listners['Listeners']:
        if (x['Port'] == 443):
            livelistenerarn = x['ListenerArn']
        if (x['Port'] == 80):
            livelistenerarn = x['ListenerArn']
        if (x['Port'] == 8443):
            betalistenerarn = x['ListenerArn']
        if (x['Port'] == 8080):
            betalistenerarn = x['ListenerArn']

    livetgresponse = elbclient.describe_rules(ListenerArn=livelistenerarn)

    for x in livetgresponse['Rules']:
        if x['Priority'] == '1':
            livetargetgroup = x['Actions'][0]['TargetGroupArn']
            liverulearn = x['RuleArn']

    betatgresponse = elbclient.describe_rules(ListenerArn=betalistenerarn)

    for x in betatgresponse['Rules']:
        if x['Priority'] == '1':
            betatargetgroup = x['Actions'][0]['TargetGroupArn']
            betarulearn = x['RuleArn']

    print("Live=" + livetargetgroup)
    print("Beta=" + betatargetgroup)

    modifyOnBeta = elbclient.modify_rule(
        RuleArn=betarulearn,
        Actions=[
            {
                'Type': 'forward',
                'TargetGroupArn': livetargetgroup
            }
        ]
    )

    print(modifyOnBeta)

    modifyOnLive = elbclient.modify_rule(
        RuleArn=liverulearn,
        Actions=[
            {
                'Type': 'forward',
                'TargetGroupArn': betatargetgroup
            }
        ]
    )

    print(modifyOnLive)
    modify_tags(livetargetgroup,"IsProduction","False")
    modify_tags(betatargetgroup, "IsProduction", "True")

def modify_tags(arn,tagkey,tagvalue):
    """Modifies the tags on the target groups as an identifier, after swap has been performed to indicate, 
        which target group is live and which target group is non-production

                Args:
                    arn : AWS ARN of the Target Group
                    tagkey: Key of the Tag
                    tagvalue: Value of the Tag

                Raises:
                    Exception: Any exception thrown by handler

    """

    elbclient.add_tags(
        ResourceArns=[arn],
        Tags=[
            {
                'Key': tagkey,
                'Value': tagvalue
            },
        ]
    )

if __name__ == "__main__":
    swaptargetgroups(ALB_NAME)