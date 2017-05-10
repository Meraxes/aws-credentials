#!/usr/bin/python
import os
import re
import sys
import shutil
import boto3
import time
from configobj import ConfigObj

from optparse import OptionParser


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

class Keys(object):
    def __init__(self, Access, Secret, Token):
        self.Access = Access
        self.Secret = Secret
        self.Token = Token

if os.path.isfile(os.path.dirname(os.path.abspath(__file__)) +  "/config.ini"):

    Options = Struct(**ConfigObj(os.path.dirname(os.path.abspath(__file__)) + "/config.ini"))

    Parser = OptionParser()
    Parser.add_option("-t", "--token", dest="MfaToken",
                      help="""MFA token for custom authentication.
                              Role based authentication will be used
                              by default.""")
    (ParserOptions, Args) = Parser.parse_args()

    if ParserOptions.MfaToken:
        Options.MfaToken = ParserOptions.MfaToken

    if not hasattr(Options, "ProfileName"):
        Options.ProfileName = "default"

else:

    Parser = OptionParser()
    Parser.add_option("-h", "--home", dest="HomeDir",
                      help="Path to your local home directory")
    Parser.add_option("-p", "--profile", dest="ProfileName",
                      help="""AWS credential profile name. Default will
                              be used if not provided.""")
    Parser.add_option("-u", "--user", dest="IamUserArn",
                      help="""MFA user for custom authentication.
                              Role based authentication will be used
                              by default.""")
    Parser.add_option("-r", "--role", dest="IamRoleArn",
                      help="""Iam role for cross account access.
                              Defaults to local IAM user account
                              if not supplied""")
    Parser.add_option("-t", "--token", dest="MfaToken",
                      help="""MFA token for custom authentication.
                              Role based authentication will be used
                              by default.""")

    (Options, Args) = Parser.parse_args()

def aws_connect(Options):

    if not Options.ProfileName:
        Options.ProfileName = "default"

    if not hasattr(Options, 'IamUserArn') and hasattr(Options, 'IamRoleArn'):

        # Cross account AWS Sydney ApiGateway client without MFA
        # Change region_name for alternate region
        try:

            # Create AWS session
            Session = boto3.session.Session(profile_name=Options.ProfileName)

            # Establish STS client for role assumption
            StsClient = Session.client('sts')

            # Assume the "AssumeRoleArn" role using STS client
            Role = StsClient.assume_role(RoleArn=Options.IamRoleArn,
                                         RoleSessionName='TempSession')

            # Extract keys and token for easier reference
            AccessKey = Role['Credentials']['AccessKeyId']
            SecretKey = Role['Credentials']['SecretAccessKey']
            SessionToken = Role['Credentials']['SessionToken']

            Response = Keys(AccessKey, SecretKey, SessionToken)

        # Light exception handler
        # Extend for additional debugging features
        except Exception as e:
            print("Cross account AWS Sydney ApiGateway client without MFA error:")
            print(e)
            sys.exit()


    if hasattr(Options, 'IamUserArn') and hasattr(Options, 'IamRoleArn'):

        # Cross account session with MFA
        # Change region_name for alternate region
        try:

            # Create AWS session
            Session = boto3.session.Session(profile_name=Options.ProfileName)

            # Establish STS client for role assumption
            StsClient = Session.client('sts')

            # Assume the "AssumeRoleArn" role using STS client
            Role = StsClient.assume_role(RoleArn=Options.IamRoleArn,
                                         RoleSessionName='TempSession',
                                         SerialNumber=Options.IamUserArn,
                                         TokenCode=Options.MfaToken)

            # Extract keys and token for easier reference
            AccessKey = Role['Credentials']['AccessKeyId']
            SecretKey = Role['Credentials']['SecretAccessKey']
            SessionToken = Role['Credentials']['SessionToken']

            Response = Keys(AccessKey, SecretKey, SessionToken)

        # Light exception handler
        # Extend for additional debugging features
        except Exception as e:
            print("Cross account session with MFA error:")
            print(e)
            sys.exit()

    return(Response)

Credentials = aws_connect(Options)
print(vars(Credentials))


fn = Options.HomeDir + "/.aws/credentials"

shutil.copyfile(fn,fn + ".orig")

with open(fn + ".orig", 'rb') as fin, open(fn, 'wb') as fout:
    data = fin.read()
    data = re.sub(r'.' + Options.NewProfile + '.*\saws.*\saws.*\s.*\s', '', data,
                  flags=re.MULTILINE)
    fout.write(data)

with open(fn, 'a') as f:
    f.write("[" + Options.NewProfile + "]\n")
    f.write("aws_access_key_id = " + Credentials.Access + "\n")
    f.write("aws_secret_access_key = " + Credentials.Secret + "\n")
    f.write("aws_security_token = " + Credentials.Token + "\n")

#  you can now source this file ". ~/bin/tmptoken.sh" to get your keys
#  and tokens in your current Shell Environment for use with local
#  Ansible development. When ~/bin is on your PATH, you can just `.
#  tmptoken.sh' and it will automatically find it.
tmptoken = Options.HomeDir + "/bin/tmptoken.sh"
with open(tmptoken, 'w') as f:
    f.write("# Last Modified: "+ time.strftime("%d/%m/%Y %H:%M:%S")+"\n")
    # f.write("# export AWS_DEFAULT_PROFILE='"+Options.NewProfile+"'\n")
    # f.write("# export AWS_DEFAULT_REGION='"+Options.NewProfile+"'\n")
    f.write("export AWS_REGION=$AWS_DEFAULT_REGION\n")
    f.write("export AWS_ACCESS_KEY_ID='"+Credentials.Access+"'\n")
    f.write("export AWS_SECRET_ACCESS_KEY='"+Credentials.Secret+"'\n")
    f.write("export AWS_SESSION_TOKEN='"+Credentials.Token+"'\n")
