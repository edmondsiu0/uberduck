#######################################################################################################################
# whichRegion.py
# Author:  @uberduck
# Created: 25 Feburary 2020
# Last modified: 25 Feburary 2020
# Source URL:
#
# This script iterate through all current AWS regions, and provide a list of AWS regions with active resources deployed.
# Default behaviour of this script is to query all AWS regions, but this can be slow and excessive.
# This behaviour can be modified by specifying --quick option which limits the regions queried to a predefined list.
#
# If no options are specified, the output does not display regions with no active resources.
# This behaviour can be overridden by the --debug option.
#
# usage: python3 whichRegion.py [--quick|--debug]
#


import boto3

# Defining variables
quick = True
debug = False
azList = []
summary = []
sortedSummary = []

session = boto3.Session(profile_name='faws_playground_edmond')
client = session.client('ec2', region_name='us-east-1')

if quick is False:

    print('Default option set, querying ALL AWS regions for resource counts. (Slow!)')
    print('Use option --quick to query selected US and EU regions only.' + '\n')

    # Retrieves all current regions within AWS
    responseRegions = client.describe_regions()

    # Set regionList to all current regions within AWS
    regionList = responseRegions['Regions']

    # Print out number of AWS Regions found
    print('Found ' + str(len(responseRegions['Regions'])) + ' AWS regions.' + '\n' + 'Querying, please wait...')

else:
    print('Quick mode, querying only the following regions:')
    print('us-east-1, us-east-2, us-west-1, us-west-2, eu-west-1, eu-west-2, eu-central-1. ' + '\n')
    print('Unset option --quick to query all AWS regions for resource counts. (slow!)' + '\n')

    # Set regions
    responseRegions = {'Regions': [
        {'Endpoint': 'ec2.eu-west-2.amazonaws.com', 'RegionName': 'eu-west-2', 'OptInStatus': 'opt-in-not-required'},
        {'Endpoint': 'ec2.eu-west-1.amazonaws.com', 'RegionName': 'eu-west-1', 'OptInStatus': 'opt-in-not-required'},
        {'Endpoint': 'ec2.eu-central-1.amazonaws.com', 'RegionName': 'eu-central-1', 'OptInStatus': 'opt-in-not-required'},
        {'Endpoint': 'ec2.us-east-1.amazonaws.com', 'RegionName': 'us-east-1', 'OptInStatus': 'opt-in-not-required'},
        {'Endpoint': 'ec2.us-east-2.amazonaws.com', 'RegionName': 'us-east-2', 'OptInStatus': 'opt-in-not-required'},
        {'Endpoint': 'ec2.us-west-1.amazonaws.com', 'RegionName': 'us-west-1', 'OptInStatus': 'opt-in-not-required'},
        {'Endpoint': 'ec2.us-west-2.amazonaws.com', 'RegionName': 'us-west-2', 'OptInStatus': 'opt-in-not-required'}]}
    regionList = responseRegions['Regions']

    print('Querying ' + str(len(responseRegions['Regions'])) + ' regions, please wait...')


# Defining reusable countResources function.
# Supports resource type 'ec2', 'rds' and 'elbv2'
def countResources(region, type):
    awsSession = session.client(type, region_name=region)

    if type is 'ec2':
        # Query AWS to get a list of running EC2 instances
        response = awsSession.describe_instances(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['running']
                }
            ]
        )
        resourceCount = len(response['Reservations'])

    elif type is 'rds':
        # Query AWS to get a list of RDS instances
        response = awsSession.describe_db_instances()
        resourceCount = len(response['DBInstances'])

    elif type is 'elbv2':
        # Query AWS to get a list of ELBv2 resources
        response = awsSession.describe_load_balancers()
        resourceCount = len(response['LoadBalancers'])

    else:
        # Return error if resource type is unsupported
        return -1

    return resourceCount


# Iterate through regionList and perform resource counting
for r in regionList:
    regionName = r['RegionName']

    ec2Count = countResources(region=regionName, type='ec2')
    rdsCount = countResources(region=regionName, type='rds')
    elbCount = countResources(region=regionName, type='elbv2')

    # (EXPERIMENTAL) Generate score for each region based on number of resources found
    # Each RDS weights 5, ELBv2 weights 2, EC2 weights 1
    # Used for ranking regions and discarding regions with no resources
    regionScore = (5 * rdsCount) + (2 * elbCount) + (1 * ec2Count)

    output = {
        'region': regionName,
        'ec2': ec2Count,
        'elb': elbCount,
        'rds': rdsCount,
        'score': regionScore
    }

    if debug is True:
        summary.append(dict(output))
    elif quick is True:
        summary.append(dict(output))
    else:
        if regionScore > 0:
            summary.append(dict(output))
        else:
            pass

# Sort region list based on score of regions
sortedSummary = sorted(summary, key=lambda i: i['score'], reverse=True)

# Print output header
print('{:<15s}{:>6s}{:>5s}{:>5s}'.format('Region', 'EC2', 'ELB', 'RDS'))

# Print output body
for s in sortedSummary:
    region = s['region']
    ec2Count = s['ec2']
    elbCount = s['elb']
    rdsCount = s['rds']
    score = s['score']

    print('{:<15s}{:>5d}{:>5d}{:>5d}'.format(region, ec2Count, elbCount, rdsCount))
