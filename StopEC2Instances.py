import boto3
from time import sleep
region = 'eu-west-1'

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name=region)
    asg = boto3.client('autoscaling', region_name=region)
    ec2_instance = boto3.resource('ec2', region_name=region)
    
    instances = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag-key',
                'Values':[ 'stop_out_of_hours'],
                'Name': 'tag-value',
                'Values':[ 'true']
            },
            {
                'Name': 'tag-key',
                'Values':[ 'role'],
                'Name': 'tag-value',
                'Values':[ 'ADS', 'FS', 'RAPPRI', 'RMQPRI', 'RMQSEC']
            }
        ],
    )

    dbs_primary_instances = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag-key',
                'Values':[ 'stop_out_of_hours'],
                'Name': 'tag-value',
                'Values':[ 'true']
            },
            {
                'Name': 'tag-key',
                'Values':[ 'role'],
                'Name': 'tag-value',
                'Values':[ 'DBSPRI']
            }
        ],
    )

    dbs_secondary_instances = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag-key',
                'Values':[ 'stop_out_of_hours'],
                'Name': 'tag-value',
                'Values':[ 'true']
            },
            {
                'Name': 'tag-key',
                'Values':[ 'role'],
                'Name': 'tag-value',
                'Values':[ 'DBSSEC']
            }
        ],
    )

    InstanceIDs = []
    for r in instances['Reservations']:
        for i in r['Instances']:
            InstanceID = i['InstanceId']
            InstanceIDs.append(InstanceID)

    DBSPrimaryInstanceIDs = []
    for r in dbs_primary_instances['Reservations']:
        for i in r['Instances']:
            InstanceID = i['InstanceId']
            DBSPrimaryInstanceIDs.append(InstanceID)

    DBSSecondaryInstanceIDs = []
    for r in dbs_secondary_instances['Reservations']:
        for i in r['Instances']:
            InstanceID = i['InstanceId']
            DBSSecondaryInstanceIDs.append(InstanceID)

    ec2.stop_instances(InstanceIds=InstanceIDs)
    
    print ('stopped your instances: ' + str(InstanceIDs))

    ec2.stop_instances(InstanceIds=DBSSecondaryInstanceIDs)

    for r in dbs_secondary_instances['Reservations']:
        for i in r['Instances']:
            InstanceID = i['InstanceId']
            instance = ec2_instance.Instance(InstanceID)
            while instance.state['Name'] not in ('stopped'):
                print ('waiting for dbs secondary instance to stop')
                sleep(5)
                instance.load()

    print ('stopped your dbs secondary instances: ' + str(DBSSecondaryInstanceIDs))

    ec2.stop_instances(InstanceIds=DBSPrimaryInstanceIDs)

    print ('stopped your dbs primary instances: ' + str(DBSPrimaryInstanceIDs))

    asgs = asg.describe_tags(
        Filters=[
            {
                'Name': 'key',
                'Values':[ 'stop_out_of_hours'],
                'Name': 'value',
                'Values':[ 'true']
            },
        ],
    )
    
    asg_ids = []
    for t in asgs['Tags']:
        ResourceID =  t['ResourceId']
        asg_ids.append(ResourceID)

    for asg_id in asg_ids:
        response = asg.update_auto_scaling_group(
            AutoScalingGroupName=asg_id,
            MinSize=0,
            MaxSize=0,
            DesiredCapacity=0
        )

        print(response)
    
    
    
