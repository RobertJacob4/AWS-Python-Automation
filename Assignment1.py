#!/usr/bin/env python3

import boto3
import colorama
import requests
import subprocess
import webbrowser
import socket
# Coloring command line text
from colorama import Fore
colorama.init(autoreset=True)
import time 

# timestamp for unique IDs
ts = time.strftime("%Y%m%d-%H%M")


ec2 = boto3.resource('ec2')
ec2Client = boto3.client('ec2')
s3 = boto3.resource('s3')
s3client = boto3.client('s3')


# Launch New EC2 Instance
try:

    instance = ec2.create_instances(
    ImageId='ami-05cd35b907b4ffe77',  # new AMI
    MinCount=1,
    MaxCount=1,
    KeyName='RJ_key',  #Key for SSH Access
    SecurityGroupIds=['sg-0a8c14d5c6be4ace3'],
    InstanceType='t2.nano',
    TagSpecifications=[

        { 
          'ResourceType':'instance',
          'Tags': [
              {
                'Key':'name',
                'Value':'assignment1'
            },]
        },],

    # Launch HTTP Server and print meta-data to web index page
    UserData = '''#!/bin/bash \n
			            sudo yum update -y
                        sudo yum install httpd -y
                        sudo systemctl enable httpd
                        sudo systemctl start httpd

					    echo '<html>' > index.html
					    echo 'Instance Meta Data: ' >> index.html
                        echo 'Private IP Address: ' >> index.html
					    curl http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html
                        echo '\n Instance ID: ' >> index.html
                        curl http://169.254.169.254/latest/meta-data/instance-id >> index.html
                        echo '\n Availabilty Zone: ' >> index.html
                        curl http://169.254.169.254/latest/meta-data/placement/availability-zone >> index.html
                        echo '\n Instance Type: ' >> index.html
                        curl http://169.254.169.254/latest/meta-data/instance-type >> index.html
                        cp index.html /var/www/html/index.html
                         ''')


    # wait for instance to launch and refresh to update details
    print(f'{Fore.YELLOW}Waiting for instance to launch...')
    instance[0].wait_until_running()
    instance[0].reload()

    # print instance details - ID and IP
    print(f'{Fore.GREEN}Instance successfully launched')
    print(f'{Fore.CYAN}Instance ID: ' + instance[0].id)
    print(f'{Fore.CYAN}Instance IP : ' + instance[0].public_ip_address)
except Exception as error:
    print (error)             


# Create New S3 bucket
def createBucket():
    try:
        bucket = s3.create_bucket(
            Bucket=f'devops-assign1-{ts}',
            ACL='public-read',
            CreateBucketConfiguration={
             'LocationConstraint':'eu-west-1'
             })

        fileName = 'assign1.jpg'
    # Download Image from URL
        request = requests.get("http://devops.witdemo.net/assign1.jpg", allow_redirects=True)
        open(fileName, 'wb').write(request.content)
    
    # S3 URL of Image file
        URL = "https://%s.s3.%s.amazonaws.com/%s" % (f"devops-assign1-{ts}", "eu-west-1", "assign1.jpg")

    # Create Index file
        subprocess.run("echo ' <html>  <img src=%s alt=\"assign1.jpg\">  </html>' > index.html" % (URL),shell=True)
        print(f'{Fore.YELLOW}Waiting for S3 bucket to Launch...')
        bucket.wait_until_exists()

    # Upload Index file and Image to S3 bucket
        s3.Object(f'devops-assign1-{ts}','index.html').put(Body=open('index.html','rb'),ACL='public-read',ContentType='text/html')
        s3.Object(f'devops-assign1-{ts}', 'assign1.jpg').put(Body=open('assign1.jpg','rb'), ACL='public-read')
     
    # Configure website
        s3client.put_bucket_website(Bucket=f'devops-assign1-{ts}', WebsiteConfiguration= {'IndexDocument': {'Suffix': 'index.html'},})
        print(f'{Fore.GREEN}S3 Bucket Launched')

    except Exception as error:
        print(error)


def launchBrowser():
    # Open Browser tabs to display HTTP Server and S3 Bucket 
    try:
       webbrowser.open_new_tab('http://%s' % (instance[0].public_ip_address))
       webbrowser.open_new_tab(f'http://devops-assign1-{ts}.s3-website-eu-west-1.amazonaws.com')  
    except Exception as error:
       print(error) 


# Check Connection to SSH is available and run Monitor Script
def connectSSH():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssh_status = "ssh unavailable"
    while ssh_status == "ssh unavailable":
        try:
           s.connect((instance[0].public_ip_address, 22)) # connect host to destination port
           print (f'{Fore.GREEN}ssh connection available')
           ssh_status = "available"
        except socket.error as e:
           print(f"{Fore.RED}Error on port 22")
    s.close()

    if ssh_status == 'available':
        #waiter = ec2Client.get_waiter('instance_status_ok')
        #waiter.wait(InstanceIds = [instance[0].id])
        scp = "scp  -o StrictHostKeyChecking=no -i RJ_key.pem monitor.sh ec2-user@%s:." % (instance[0].public_ip_address)
        subprocess.run(scp, shell=True)
        permission = "ssh -o StrictHostKeyChecking=no -i RJ_key.pem ec2-user@%s 'chmod 700 monitor.sh' " % (instance[0].public_ip_address)
        subprocess.run(permission, shell=True)
        runScript = "./monitor.sh"
        subprocess.run(runScript, shell=True)
        print(f'{Fore.GREEN}Monitoring script uploaded and ran successfully')

    

createBucket()  
launchBrowser()
connectSSH()

        




        
