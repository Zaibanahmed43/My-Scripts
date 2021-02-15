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
                'Name': 'tag:stop_out_of_hours',
                'Values':['true'],
            },
            {
                'Name': 'role',
                'Values':[ 'ADS', 'FS', 'PRI', 'RMQPRI', 'RMQSEC']
            }
        ],
    )
    
    dbs_primary_instances = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag:stop_out_of_hours',
                'Values':[ 'true'],
            },
            {
                'Name': 'role',
                'Values':[ 'DBSPRI'],
            }
        ],
    )

    dbs_secondary_instances = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag:stop_out_of_hours',
                'Values':[ 'true'],
            },
            {
                'Name': 'role',
                'Values':[ 'DBSSEC'],
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

    ec2.start_instances(InstanceIds=DBSPrimaryInstanceIDs)

    for r in dbs_primary_instances['Reservations']:
        for i in r['Instances']:
            InstanceID = i['InstanceId']
            instance = ec2_instance.Instance(InstanceID)
            while instance.state['Name'] not in ('running'):
                print ('waiting for dbs primary instance to start')
                sleep(5)
                instance.load()
            
    print ('started your DBS primary instances: ' + str(DBSPrimaryInstanceIDs))

    ec2.start_instances(InstanceIds=DBSSecondaryInstanceIDs)

    print ('started your DBS secondary instances: ' + str(DBSSecondaryInstanceIDs))

    ec2.start_instances(InstanceIds=InstanceIDs)
    
    print ('started your instances: ' + str(InstanceIDs))
    
    asgs = asg.describe_tags(
        Filters=[
            {
                'Name': 'tag:stop_out_of_hours',
                'Values':[ 'true'],
            },
        ],
    )
    
    asg_ids = []

    for t in asgs['Tags']:
        ResourceID =  t['ResourceId']
        asg_ids.append(ResourceID)

    for asg_id in asg_ids:
        if asg_id == "ASG-ID":
            response = asg.update_auto_scaling_group(
                AutoScalingGroupName=asg_id,
                MinSize=1,
                MaxSize=2,
                DesiredCapacity=1
            )
        elif asg_id == "ASG-ID":
            response = asg.update_auto_scaling_group(
                AutoScalingGroupName=asg_id,
                MinSize=6,
                MaxSize=6,
                DesiredCapacity=6
            )
        else:
            response = asg.update_auto_scaling_group(
                AutoScalingGroupName=asg_id,
                MinSize=2,
                MaxSize=2,
                DesiredCapacity=2
            )
        print(response)
