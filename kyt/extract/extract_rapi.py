import sys
import os
import collections
import re
import requests
import logging
logger = logging.getLogger(__name__) 

import functools
import common.timewatch

class RestApiException(Exception):
    pass


TApiConfig = collections.namedtuple( "TApiConfig", [ "server", "port", "base" ] )
TApiAuthent = collections.namedtuple( "TApiAuthent", [ "login", "password", "apikey"] )

# Parameters:
#   0: rest api server address or name
#   1: port number
#   2: restapi name
C_URL_RESTAPI_BASE = "http://{0}:{1}/{2}/rest"
C_SNAPSHOTS = "/snapshots"
C_ADGDATABASE = "adgDatabase"
C_NAME ="name"
C_DBTYPE="dbType"
C_PATH_CRITICAL_VIOLATIONS_BY_BC="/violations?rule-pattern=critical-rules&business-criterion={0}&startRow={1}&nbRows={2}"
C_PATH_CRITICAL_VIOLATIONS_BY_BC="/violations?rule-pattern=cc:{0}&startRow={1}&nbRows={2}"
# Trhought lucene index
C_PATH_CRITICAL_VIOLATIONS_BY_BC="/violations-index?startRow={1}&nbRows={2}"
# From snapshot
C_PATH_ALL_VIOLATIONS_BY_BC="AED/applications/3/snapshots/8/indexed-violations?startRow=1&nbRows=1000"

V_PERFORMANCES=[]

def kyt_perf( aLabel=__name__ ):
    def decorator_perf( aF ):
        @functools.wraps(aF)
        def wrapper( *args, **kwargs ):
            vWatchTr = common.timewatch.TimeWatch()
            retVal = aF(*args, **kwargs)
            vWatchTr.stop()
            V_PERFORMANCES.append( ( aLabel, vWatchTr.deltaElapsed(), vWatchTr.deltaCpu() ))
            return retVal
        return wrapper
    return decorator_perf

@kyt_perf("rest-api-query")
def restExecuteQuery( aApiCfg, aAuth, aPath ):
    retVal = None
    vBase = C_URL_RESTAPI_BASE.format(aApiCfg.server,aApiCfg.port,aApiCfg.base)
    vUrl = "{}/{}".format(vBase,aPath)
    logger.info( "      invoking query: {}".format(vUrl) )
    vResp = requests.get( vUrl, auth=(aAuth.login, aAuth.password), headers={"content-type":"application/json","accept":"application/json"} )
    
    if 200 != vResp.status_code:
        print( "***ERROR: {}".format(vResp.status_code), file=sys.stderr )
    else:
        #logger.info( "content-type: {}".format(vResp.headers["content-type"]) )
        if "application/json" == vResp.headers["content-type"]:
            retVal = vResp.json()
        else:
            logger.info( "***ERROR: don't support response's content-type: {}".format(vResp.headers["content-type"]) )

    return retVal

@kyt_perf("rest-api-critical-violations")
def extractCriticalViolationsOfTransaction( aApiCfg, aApiAuth, aTrHref, aBc=60017 ):
    vStartRow = 1
    vNbRows = 5000
    vRowsRecv = vNbRows
    if vRowsRecv >= vNbRows:
        vRowsRecv = 0
        vPath = C_PATH_CRITICAL_VIOLATIONS_BY_BC.format(aBc,vStartRow,vNbRows)
        vResp = restExecuteQuery( aApiCfg, aApiAuth, aTrHref+vPath )
        if vResp:
            logger.info( "      found critical violations: {}".format(len(vResp)) )
        for i in vResp:
            yield i
            vRowsRecv += 1
        vStartRow += vRowsRecv

@kyt_perf("rest-api-all-violations")
def extractAllViolationsOfTransaction( aApiCfg, aApiAuth, aTrHref, aBc=60017 ):
    vStartRow = 1
    vNbRows = 100000
    vRowsRecv = vNbRows
    if vRowsRecv >= vNbRows:
        vRowsRecv = 0
        vPath = C_PATH_ALL_VIOLATIONS_BY_BC.format(aBc,vStartRow,vNbRows)
        vResp = restExecuteQuery( aApiCfg, aApiAuth, aTrHref+vPath )
        if vResp:
            logger.info( "      found violations: {}".format(len(vResp)) )
        for i in vResp:
            yield i
            vRowsRecv += 1
        vStartRow += vRowsRecv

@kyt_perf("rest-api-get-application")
def getApplicationHRef( aApiCfg, aApiAuth, aAppName, aAppSchemaBasename ):
    # Searching for entries of dbtype ADG having right name or right app schema
    vAedApplication = None
    vAedApplications = []
    for i in restExecuteQuery( aApiCfg, aApiAuth, "" ):
        logger.info( "        resp entry: {}".format(str(i)) )
        if C_DBTYPE in i and "ADG"==i[C_DBTYPE]:
            vAedApplications.append( i["applications"]["href"] )

    for iA in vAedApplications:
        if iA:
            for i in restExecuteQuery( aApiCfg, aApiAuth, iA ):
                logger.info( "        resp entry: {}".format(str(i)) )
                if ( aAppName and C_NAME in i and i[C_NAME]==aAppName ) \
                    or ( aAppSchemaBasename and C_ADGDATABASE in i and i[C_ADGDATABASE]==aAppSchemaBasename+"_central"):
                    vAedApplication = i["href"]
                    break
    return vAedApplication

# Extract latest snapshot (based on snapshot number)
@kyt_perf("rest-api-get-snapshot")
def getLatestSnapshot( aApiCfg, aApiAuth, aAppHref ):
    retVal = None
    vMaxSnapshotNumber = -1
    for iN, i in enumerate(restExecuteQuery( aApiCfg, aApiAuth, aAppHref+C_SNAPSHOTS)):
        if i["number"] > vMaxSnapshotNumber:
            retVal = i
            vMaxSnapshotNumber = i["number"]
    return retVal

@kyt_perf("rest-api-search-transaction")
def searchTransaction( aApiCfg, aApiAuth, aSnapshotHRef, aTrFullname ):
    retVal = None
    for iN,iTr in enumerate(restExecuteQuery( aApiCfg, aApiAuth, aSnapshotHRef+"/transactions/"+str(60017)+"?startRow=1&nbRows=1000" )):
        if iTr["name"] == aTrFullname:
            retVal = iTr
            break
    return retVal

@kyt_perf("30_objects-with-violations2.txt")
def extractCriticalViolations( aOptions, aApiCfg, aApiAuth, aTransaction ):
    logger.info( "      writing to [{}]".format(os.path.join(aOptions['tr-output-data-folder'], "30_objects-with-violations2.txt") ) )
    with open( os.path.join( aOptions['tr-output-data-folder'], "30_objects-with-violations2.txt"), "w") as vOF:
        vRxObjectId = re.compile( r"[^/]+/components/([0-9]+)/snapshots/([0-9]+)" )
        vRxRuleId = re.compile( r"[^/]+/rule-patterns/([0-9]+)" )
        print( "#LocalObjectId|CentralObjectId|MetricId|isCritical|BCriterionId|TCriterionId|ObjectName|ObjectFullname|BCriterionName|TCriterionName|MetricName|SnapshotId|ObjectDesc", file=vOF )
        for iN, iCV in enumerate(extractCriticalViolationsOfTransaction( aApiCfg, aApiAuth, aTransaction["href"] )):
            #print( iN, ":", iCV )
            try:
                vObjectName = iCV["component"]["shortName"]
                vObjectFullname = iCV["component"]["name"]
                vRes = vRxObjectId.match(iCV["component"]["href"])
                if vRes:
                    vCentralObjectId = int(vRes[1])
                    vSnapshotId = int(vRes[2])
                else:
                    raise NameError("component@objectId")
                vCentralObjectId = None
                vRuleId = None
                vSnapshotId = None
                vRes = vRxRuleId.match(iCV["rulePattern"]["href"])
                if vRes:
                    vRuleId = int(vRes[1])
                else:
                    raise NameError("rulePattern@metricId")
                vMetricName = iCV["rulePattern"]["name"]
                print( "*?*|{}|{}|Yes|*?*|*?*|{}|{}|*?*|*?*|{}|{}|*?*".format(vCentralObjectId,vRuleId,vObjectName,vObjectFullname,vMetricName,vSnapshotId), file=vOF )
            except ( KeyError, NameError ) as xX:
                logger.warning( "! Warning: could not retrieve critical violation: {}: {}: {}: {}".format(iN,type(xX),xX,iCV) )

@kyt_perf("32_object-violations2.txt")
def extractAllViolations( aOptions, aApiCfg, aApiAuth, aTransaction ):
    logger.info( "      writing to [{}]".format( os.path.join(aOptions['tr-output-data-folder'], "32_object-violations2.txt") ) )
    with open( os.path.join( aOptions['tr-output-data-folder'], "32_object-violations2.txt"), "w") as vOF:
        vRxObjectId = re.compile( r"[^/]+/components/([0-9]+)/snapshots/([0-9]+)" )
        vRxRuleId = re.compile( r"[^/]+/rule-patterns/([0-9]+)" )
        print( "#0/A:LocalObjectId|1/B:ObjectName|2/C:CentralObjectId|3/D:MetricId|4/E:MetricName|5/F:BCriterionId|6/G:BCriterionName|7/H:TCriterionId|8/I:TCriterionName|9/J:TWeight|10/K:MWeight|11/L:TCrit|12/M:MCrit|13/N:TransactionId|14/O:TransactionName|15/P:ObjectFullname|16/Q:TransactionFullname", file=vOF )
        for iN, iCV in enumerate(extractAllViolationsOfTransaction( aApiCfg, aApiAuth, aTransaction["href"] )):
            #print( iN, ":", iCV )
            try:
                vObjectName = iCV["component"]["shortName"]
                vObjectFullname = iCV["component"]["name"]
                vRes = vRxObjectId.match(iCV["component"]["href"])
                if vRes:
                    vCentralObjectId = int(vRes[1])
                    vSnapshotId = int(vRes[2])
                else:
                    raise NameError("component@objectId")
                vCentralObjectId = None
                vRuleId = None
                vSnapshotId = None
                vRes = vRxRuleId.match(iCV["rulePattern"]["href"])
                if vRes:
                    vRuleId = int(vRes[1])
                else:
                    raise NameError("rulePattern@metricId")
                vMetricName = iCV["rulePattern"]["name"]
                print( "*?*|{}|{}|Yes|*?*|*?*|{}|{}|*?*|*?*|{}|{}|*?*".format(vCentralObjectId,vRuleId,vObjectName,vObjectFullname,vMetricName,vSnapshotId), file=vOF )
            except ( KeyError, NameError ) as xX:
                logger.warning( "! Warning: could not retrieve critical violation: {}: {}: {}: {}".format(iN,type(xX),xX,iCV) )

def extractTransactionData( aOptions, aPerformances ):
    logger.info( "    - Extracting facts from REST API..." )
    retVal = False  # True if violations have been loaded

    vWatch = common.timewatch.TimeWatch()
    
    # get options
    if "rest-api" in aOptions and aOptions['with-violations']:
        vApiConfiguration = TApiConfig(aOptions["rest-api"]["server"],aOptions["rest-api"]["port"],aOptions["rest-api"]["base"])
        vApiAuthentication = TApiAuthent(aOptions["rest-api"]["login"],aOptions["rest-api"]["password"],aOptions["rest-api"]["apikey"])
        logger.info( "    using REST: server='{}', port={}, base='{}', login='{}', password='{}', apikey='{}'".format(
            vApiConfiguration.server, vApiConfiguration.port, vApiConfiguration.base, vApiAuthentication.login, vApiAuthentication.password, vApiAuthentication.apikey ) )
        
        # Get application href
        vAppHRef = getApplicationHRef( vApiConfiguration, vApiAuthentication, "", aOptions["db-schema-prefix"] )

        if vAppHRef:
            logger.info( "      -> using application: {}".format(vAppHRef) )
            # Get snapshot href
            vSnapshot = getLatestSnapshot(vApiConfiguration,vApiAuthentication,vAppHRef)
            logger.info( "      -> using snaphot: {}: {}: {}".format(vSnapshot["number"],vSnapshot["href"],vSnapshot["annotation"]["version"]) )

            vTransactionSearchCriteria = aOptions['transaction-criteria']
            vTransactionSearchValue = aOptions['transaction-criteria-value']
            if vTransactionSearchCriteria == "fullname":
                vTransaction = searchTransaction( vApiConfiguration, vApiAuthentication, vSnapshot["href"], vTransactionSearchValue)
                if vTransaction:
                    logger.info( "      -> using transaction: {}".format(vTransaction) )
                    extractCriticalViolations( aOptions, vApiConfiguration, vApiAuthentication, vTransaction )
                    extractAllViolations( aOptions, vApiConfiguration, vApiAuthentication, vTransaction )
                    retVal = True
                else:
                    logger.error( "***ERROR: could not find transaction via REST API: {}".format(vTransactionSearchValue) )
            else:
                logger.error( "***ERROR: criteria not supported for REST API: {}".format(vTransactionSearchCriteria) )
        else:
            logger.error( "***ERROR: could not find application via REST API" )
            raise RestApiException()

    vWatch.stop()
    aPerformances.extend( V_PERFORMANCES )
    aPerformances.append( ( "extraction-rapi", vWatch.deltaElapsed(), vWatch.deltaCpu() ))
    return retVal
