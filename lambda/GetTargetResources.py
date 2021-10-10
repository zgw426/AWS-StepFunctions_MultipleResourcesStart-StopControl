import json
import datetime
import boto3

## --------- ↓↓↓ 関数 ↓↓↓ --------- ##
# 対象のEC2インスタンスの情報を取得
def searchEc2Tag( returnValue, GroupTag, GroupVal, BootOrderTag, ExecVal ):
    client = boto3.client('ec2')
    NextToken = None
    while True:
        if NextToken is None:
            response = client.describe_instances()
        else:
            response = client.describe_instances(NextToken=NextToken)

        for Reservations in response['Reservations']:
            for instances in Reservations['Instances']:
                addFlg = 0
                tmpValue = {}
                BootNo = 0
                NameVal = ""
                for tag in instances['Tags']:
                    if tag["Key"] == GroupTag and tag["Value"] == GroupVal:
                        GroupVal = tag["Value"]
                        addFlg = 1
                        print("addFlg = 1")
                    elif tag["Key"] == BootOrderTag:
                        BootNo = int(tag["Value"])
                    elif tag["Key"] == "Name":
                        NameVal = tag["Value"]
                if addFlg == 1:
                    tmpValue["ID"] = str(instances['InstanceId'])
                    tmpValue["ResourceType"] = "EC2"
                    tmpValue["Name"] = NameVal
                    tmpValue["Group"] = GroupVal
                    tmpValue["BootOrder"] = BootNo
                    tmpValue["EXEC"] = ExecVal
                    returnValue.append(tmpValue)
        if not 'NextToken' in response:
            break
        NextToken = response['NextToken']
    return 0

# 対象のRDSクラスターの情報を取得
def searchRdsTag( returnValue, GroupTag, GroupVal, BootOrderTag, ExecVal ):
    client = boto3.client('rds')
    NextToken = None
    while True:
        if NextToken is None:
            response = client.describe_db_clusters()
        else:
            response = client.describe_db_clusters(Marker=Marker)

        for Reservations in response['DBClusters']:
            addFlg = 0
            tmpValue = {}
            BootNo = 0
            NameVal = ""
            for tag in Reservations['TagList']:
                if tag["Key"] == GroupTag and tag["Value"] == GroupVal:
                    GroupVal = tag["Value"]
                    addFlg = 1
                elif tag["Key"] == BootOrderTag:
                    BootNo = int(tag["Value"])
                elif tag["Key"] == "Name":
                    NameVal = tag["Value"]
            print("addFlg = {0}".format(addFlg))
            if addFlg == 1:
                tmpValue["ID"] = str(Reservations["DBClusterIdentifier"])
                tmpValue["ResourceType"] = "Aurora"
                tmpValue["Name"] = NameVal
                tmpValue["Group"] = GroupVal
                tmpValue["BootOrder"] = BootNo
                tmpValue["EXEC"] = ExecVal
                returnValue.append(tmpValue)
        if not 'Marker' in response:
            break
        Marker = response['Marker']
    return 0

## --------- ↑↑↑↑ 関数 ↑↑↑ --------- ##

def lambda_handler(event, context):
    if event["DATE"] == "now":
        dt_now = datetime.datetime.now()
        dt_now = dt_now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        event["DATE"] = dt_now
    
    resources = {}
    resources["EXEC"] = event["EXEC"]
    resources["DATE"] = event["DATE"]
    resources["TARGETS"] = []

    searchEc2Tag( resources["TARGETS"], event["GroupTag"], event["GroupValue"], event["BootOrderTag"], event["EXEC"] )
    searchRdsTag( resources["TARGETS"], event["GroupTag"], event["GroupValue"], event["BootOrderTag"], event["EXEC"] )

    # EXEC値により TARGETS 配下を並べ替え
    if event["EXEC"] == "start":
        resources["TARGETS"] = sorted(resources["TARGETS"], key=lambda x: x['BootOrder'])
    elif event["EXEC"] == "stop":
        resources["TARGETS"] = sorted(resources["TARGETS"], key=lambda x: x['BootOrder'], reverse=True)
    else:
        print("error処理を入れる")

    return resources
