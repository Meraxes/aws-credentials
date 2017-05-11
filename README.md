# aws-credentials

## Prerequisites

* Call `mkdir -p ~/bin`
* Install and configure virtual MFA on your device.

## Example

* Copy config.ini.example to config.ini
* Update config.ini
```
## config.ini

# Your user's home directory on your workstation
HomeDir = "/cygdrive/c/Users/Felipe/cygwin64/home/Felipe"

# the profile to read from your ~/.aws/credentials file
ProfileName = "itoc"

# the profile to append to your ~/.aws/credentials file
NewProfile = "osssio-staff"

# Region
Region = "ap-southeast-2"

# Your user mfa arn (source account)
IamUserArn = "arn:aws:iam::650679463300:mfa/felipe.alvarez"

# Role arn on the destination account
IamRoleArn = "arn:aws:iam::051402705597:role/ITOCAccountAccess"
```

* Run: `aws-credentials.py -t XXXXXX`

Where XXXXXX is the output of your MFA device.

* When successful, source environment variables:
`. tmptoken.sh`
