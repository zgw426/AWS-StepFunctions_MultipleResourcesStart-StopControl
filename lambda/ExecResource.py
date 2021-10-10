import json
import boto3

## --------- ↓↓↓ 関数 ↓↓↓ --------- ##
# 指定したEC2インスタンスの起動/停止
def execEC2(instanceId,execType):
    response = "ERROR"
    try:
        client = boto3.client('ec2')
        if execType == "start":
            client.start_instances( InstanceIds=[ instanceId ] )
        elif execType == "stop":
            client.stop_instances( InstanceIds=[ instanceId ] )
        response = "NEXT"
    except:
        response = "ERROR"
    return response

# RDS(Aurora)クラスターの状態確認
def getDBClusterStatus(DBClusterIdentifier):
    client = boto3.client('rds')
    res = client.describe_db_clusters( DBClusterIdentifier=DBClusterIdentifier )
    statusVal = res["DBClusters"][0]["Status"]
    response = statusVal
    #print("statusVal = {0}".format(statusVal))
    return response

# RDS(Aurora)クラスターの起動/停止
def execDBCluster(DBClusterIdentifier, execType):
    dbcStatus = getDBClusterStatus(DBClusterIdentifier)
    print( "DBClusterStatus = {0}".format( dbcStatus) )
    response = "ERROR" # 初期値
    try:
        if dbcStatus == "stopped" and execType == "stop":
            response = "NEXT"
        elif dbcStatus == "available" and execType == "start":
            response = "NEXT"
        else:
            client = boto3.client('rds')
            if execType == "stop": # 停止命令の場合
                client.stop_db_cluster( DBClusterIdentifier=DBClusterIdentifier )
            elif execType == "start": # 起動命令の場合
                client.start_db_cluster( DBClusterIdentifier=DBClusterIdentifier )
            response = "NEXT"
    except:
        response = "ERROR"
    print("[RDS-Aurora] response = {0}".format(response) )
    return response
## --------- ↑↑↑↑ 関数 ↑↑↑ --------- ##

def lambda_handler(event, context):
    ResourceType = event["ResourceType"]
    IdVal   = event["ID"]
    ExecVal = event["EXEC"]

    if ResourceType == "EC2":
        event["RESPONSE"] = execEC2( IdVal , ExecVal )
    elif ResourceType == "Aurora":
        event["RESPONSE"] = execDBCluster( IdVal , ExecVal )
    return event
