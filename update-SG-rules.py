import boto3
from sys import argv as ENV

class SecurityGroupUpdate(object):
    def __init__(self, ip, user, sec_group):
        self.ip = ip
        self.user = user
        self.sec_id = sec_group
        self.region = 'AWS REGION'
        self.access_key = 'AWS ACCESS KEY'
        self.secret_key = 'AWS SECRET KEY'

    def create_client(self):
        client = boto3.client('ec2',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )
        return client

    def find_remove_rule(self, client):
        data = client.describe_security_groups(GroupIds=[self.sec_id])
        rules = data['SecurityGroups'][0]['IpPermissions']
        for rule in rules:
            if rule['IpRanges'][0].get('Description') == self.user:
                self.remove_rule(client, rule)

    def remove_rule(self, client, rule):
        response = client.revoke_security_group_ingress(
            GroupId=self.sec_id,
            IpPermissions=[rule]
        )
        print('Old Rule deleted')

    def create_rule(self, client):
        response = client.authorize_security_group_ingress(
            GroupId=self.sec_id,
            IpPermissions=[
                {
                    'FromPort': 9000,
                    'IpProtocol': 'tcp',
                    'IpRanges': [
                        {
                            'CidrIp': self.ip+'/32',
                            'Description': self.user,
                        },
                    ],
                    'ToPort': 9000,
                },
            ],
        )
        print('New Rule Added')

if __name__ == '__main__':
    a = SecurityGroupUpdate(ENV[1], ENV[2], ENV[3])
    client = a.create_client()
    a.find_remove_rule(client)
    a.create_rule(client)
