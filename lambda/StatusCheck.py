import json
import boto3

## --------- ↓↓↓ 関数 ↓↓↓ --------- ##
# 指定したEC2の [ステータスチェック] を取得
def getEc2StatusCheck( instanceId ):
    client = boto3.client('ec2')
    response = client.describe_instance_status(InstanceIds=[ instanceId ])
    rtnVal = {}
    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
        if len(response["InstanceStatuses"]) == 0:
            rtnVal["InstanceStatuses"] = "NONE"
            rtnVal["InstanceStatus"]   = "NONE"
            rtnVal["SystemStatus"]     = "NONE"
        else:
            rtnVal["InstanceStatuses"] = response["InstanceStatuses"][0]["InstanceState"]["Name"]
            # 'pending'|'running'|'shutting-down'|'terminated'|'stopping'|'stopped'
            rtnVal["InstanceStatus"]   = response["InstanceStatuses"][0]["InstanceStatus"]["Status"]
            # 'ok'|'impaired'|'insufficient-data'|'not-applicable'|'initializing'
            rtnVal["SystemStatus"]     = response["InstanceStatuses"][0]["SystemStatus"]["Status"]
            # 'ok'|'impaired'|'insufficient-data'|'not-applicable'|'initializing'
    print("[EC2] rtnVal = {0}".format(rtnVal))
    return rtnVal

# EC2の [ステータスチェック](関数 getEc2StatusCheck )の結果から次の処理を決定
def setNextStep( instanceId , execType): # [ステータスチェック]の結果でStepFunctionsの次の処理を決定
    nowStatus = getEc2StatusCheck( instanceId )
    #print(nowStatus)
    rtnVal = "NONE"
    selVal = "{0}--{1}--{2}".format(nowStatus["InstanceStatus"], nowStatus["SystemStatus"], execType)
    if nowStatus["InstanceStatuses"] == "NONE" and execType == "stop": # 停止かつ停止命令
        rtnVal = "NEXT"
    elif nowStatus["InstanceStatuses"] == "NONE" and execType == "start": # 停止かつ起動命令
        rtnVal = "WAIT"
    elif nowStatus["InstanceStatuses"] == "pending": # 保留
        rtnVal = "WAIT"
    elif nowStatus["InstanceStatuses"] == "terminated": # 削除
        rtnVal = "SKIP"
    elif nowStatus["InstanceStatuses"] == "stopping": # 停止中
        rtnVal = "WAIT"
    elif nowStatus["InstanceStatuses"] == "stopped" and execType == "stop": # 停止かつ停止命令
        rtnVal = "NEXT"
    elif nowStatus["InstanceStatuses"] == "stopped" and execType == "start": # 停止かつ起動命令
        rtnVal = "WAIT"
    elif nowStatus["InstanceStatuses"] == "shutting-down": # 停止中(?)
        rtnVal = "WAIT"
    elif nowStatus["InstanceStatuses"] == "running": # 起動or起動中
        rtnVal = "NONE"

    if rtnVal == "NONE":
        if selVal == "ok--ok--stop": # 起動かつ停止命令
            rtnVal = "WAIT"
        elif selVal == "ok--ok--start": # 起動かつ起動命令
            rtnVal = "NEXT"
        elif selVal == "NONE--NONE--stop": # 停止かつ停止命令
            rtnVal = "NEXT"
        elif selVal == "NONE--NONE--start": # 起動かつ起動命令
            rtnVal = "WAIT"
        elif "impaired" in selVal: # 障害が発生
            rtnVal = "ERROR"
        elif "insufficient-data" in selVal: # データ不足
            rtnVal = "WAIT"
        elif "not-applicable" in selVal: # ?
            rtnVal = "WAIT"
        elif "initializing" in selVal: # 初期化中
            rtnVal = "WAIT"
        else:
            rtnVal = "WAIT"
    else:
            print("[EC2](else-hit) rtnVal = {0}, selVal = {1}, execType = {2}".format(rtnVal,selVal,execType))

    print("[EC2] rtnVal = {0}, selVal = {1}, execType = {2}, nowStatus[InstanceStatuses] = {3}".format(rtnVal,selVal,execType,nowStatus["InstanceStatuses"]))

    return rtnVal # [ NEXT | WAIT | ERROR | SKIP ]

# 対象のRDSクラスターに所属するDBインスタンスを取得
def searchRdsClusterDBInstances( dbClusterId ):
    rtnVal = []
    client = boto3.client('rds')
    NextToken = None
    while True:
        if NextToken is None:
            response = client.describe_db_clusters(DBClusterIdentifier=dbClusterId)
        else:
            response = client.describe_db_clusters(DBClusterIdentifier=dbClusterId,Marker=Marker)

        for Reservations in response['DBClusters']:
            for instance in Reservations['DBClusterMembers']:
                print("instance = {0}".format(instance))
                rtnVal.append( instance["DBInstanceIdentifier"] )
        if not 'Marker' in response:
            break
        Marker = response['Marker']
    return rtnVal

def getDBInstancesStatus( dbClusterId, ExecType ):
    client = boto3.client('rds')
    allRtnVal = ""
    rtnVal    = ""
    dbInstances = searchRdsClusterDBInstances( dbClusterId )
    print("dbInstances = {0}".format(dbInstances))
    for dbInstance in dbInstances:
        statusVals = "NONE"
        srtnVal = "NONE"
        try:
            NextToken = None
            while True:
                if NextToken is None:
                    response = client.describe_db_instances(DBInstanceIdentifier=dbInstance)
                else:
                    response = client.describe_db_instances(DBInstanceIdentifier=dbInstance,Marker=Marker)
                
                for Reservations in response['DBInstances']:
                    statusVals += "-{0}-".format(Reservations["DBInstanceStatus"])
                if not 'Marker' in response:
                    break
                Marker = response['Marker']

            if statusVals == "NONE":
                srtnVal = "ERROR"
            elif "available" in statusVals and ExecType == "start":
                srtnVal = "NEXT"
            elif "available" in statusVals and ExecType == "stop":
                srtnVal = "WAIT"
            elif "stopped" in statusVals and ExecType == "start":
                srtnVal = "WAIT"
            elif "stopped" in statusVals and ExecType == "stop":
                srtnVal = "NEXT"
            elif "starting" in statusVals:
                srtnVal = "WAIT"
            elif "stopping" in statusVals:
                srtnVal = "WAIT"
            elif "configuring-enhanced-monitoring" in statusVals:
                srtnVal = "WAIT"
            elif "" in statusVals:
                srtnVal = "WAIT"
            elif "" in statusVals:
                srtnVal = "WAIT"
            elif "backing-up" in statusVals:
                srtnVal = "WAIT"
            elif "configuring-iam-database-auth" in statusVals:
                srtnVal = "WAIT"
            elif "configuring-log-exports" in statusVals:
                srtnVal = "WAIT"
            elif "converting-to-vpc" in statusVals:
                srtnVal = "WAIT"
            elif "creating" in statusVals:
                srtnVal = "WAIT"
            elif "deleting" in statusVals:
                srtnVal = "WAIT"
            elif "maintenance" in statusVals:
                srtnVal = "WAIT"
            elif "modifying" in statusVals:
                srtnVal = "WAIT"
            elif "moving-to-vpc" in statusVals:
                srtnVal = "WAIT"
            elif "rebooting" in statusVals:
                srtnVal = "WAIT"
            elif "resetting-master-credentials" in statusVals:
                srtnVal = "WAIT"
            elif "renaming" in statusVals:
                srtnVal = "WAIT"
            elif "storage-optimization" in statusVals:
                srtnVal = "WAIT"
            elif "upgrading" in statusVals:
                srtnVal = "WAIT"
            else:
                srtnVal = "ERROR"
            print("[RDS-Aurora] srtnVal = {0}, statusVals = {1}, ExecType = {2}, dbInstance = {3}".format( srtnVal,statusVals,ExecType,dbInstance ) )
        except:
            srtnVal = "ERROR"
            """
            failed
            inaccessible-encryption-credentials
            incompatible-network
            incompatible-option-group
            incompatible-parameters
            incompatible-restore
            insufficient-capacity
            restore-error
            storage-full
            """
        allRtnVal += "-{0}-".format(srtnVal)
        print("[RDS-Aurora] allRtnVal = {0}".format(allRtnVal) )
        if "ERROR" in allRtnVal:
            rtnVal = "ERROR"
        elif "WAIT" in allRtnVal:
            rtnVal = "WAIT"
        else:
            rtnVal = "NEXT"
    return rtnVal

## --------- ↑↑↑↑ 関数 ↑↑↑ --------- ##

def lambda_handler(event, context):
    response = 0
    ResourceType = event["ResourceType"]
    IdVal        = event["ID"]
    ExecVal      = event["EXEC"]
    event["NextAction"] = "NONE"
    if ResourceType == "EC2":
        event["NextAction"] = setNextStep( IdVal , ExecVal ) # [ NEXT | WAIT | ERROR | SKIP ]
    elif ResourceType == "Aurora":
        event["NextAction"] = getDBInstancesStatus( IdVal , ExecVal )
    return event
