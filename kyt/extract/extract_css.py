import os
import sys
import collections
import psycopg2
import json
import logging
logger = logging.getLogger(__name__) 

import common.timewatch
import common.config

from extract import query_boilerplate
from extract import query
from extract import query_objpros
from extract import query_transactionCriticalViolations
from extract import query_transactionEndpoints
from extract import query_transactionLinks
from extract import query_transactionObjects
from extract import query_allTransactions
from extract import query_transactions
from extract import query_transactionViolations

# if this file is present, it means all load have been already done in a previous run
# So if do not override is requested and this file is present => skip
C_OVERRIDEALL_EVIDENCE="40_objects-objpro.txt"


class Acc:
    _v = None

    def sto( aExpr ):
        Acc._v = aExpr
        return Acc._v

    def v():
        retVal = Acc._v
        Acc._v = None
        return retVal



def postgresConnectionString( aDbConfig ):
    #return "host='"+aDbConfig['db-server']+"' port="+aDbConfig['db-port']+" dbname='"+aDbConfig['db-base']+"' user='"+aDbConfig['db-login']+"' password='"+aDbConfig['db-password']+"'"
    return "host='{0}' port={1} dbname='{2}' user='{3}' password='{4}'".format(
            aDbConfig['db-server'], aDbConfig['db-port'], aDbConfig['db-base'], aDbConfig['db-login'], aDbConfig['db-password']
        )

def escapePipe( aStr ):
    return aStr.replace('|','/')

##== The main job here ------------------------------------------------------
def extractTransactionData( aOptions, aLoadViolations, aPerformances ):
    logger.info( "    - Extracting facts from CSS..." )
    vLoadViolations = aOptions["force-css-violations-extract"] or aLoadViolations

    vWatchTr = common.timewatch.TimeWatch()

    queries = None

    # Do not override
    vDoNotOverride = True   # do not override file that has been already created
    vDoNotOverride = not aOptions["override-existing-extract-file"] if "override-existing-extract-file" in aOptions else True

    aCriteria = aOptions['transaction-criteria']
    aCriteriaValue = aOptions['transaction-criteria-value']
    aCriteriaOp = aOptions['transaction-criteria-op']
    aWithViolations = aOptions['with-violations']
    aOutputFolderPath = aOptions['tr-output-data-folder']
    aConfig = aOptions['db-config']
    if None != aCriteria:
        if "id" != aCriteria:
            vCriteriaValue = "'{}'".format(aCriteriaValue)
        else:
            vCriteriaValue = aCriteriaValue
            
        # Query map is intanciated with the proper criteria
        queries = [
            ( "List-of-all-transactions", False, query_allTransactions.configAllTransactions.selectQ, ( aConfig['db-local'],), query_allTransactions.configAllTransactions.selectH, "00b_all-transactions.txt", False, False, None ),
            ( "List-of-transactions", False, query_transactions.configTransactions.selectQ, ( aConfig['db-local'], vCriteriaValue, aCriteria), query_transactions.configTransactions.selectH, "01b_transactions.txt", False, False, None ),
            ( "List-of-transaction-objects", False, query_transactionObjects.configTransactionObjects.selectQ, ( aConfig['db-local'], vCriteriaValue, aCriteria, aConfig['db-central']), query_transactionObjects.configTransactionObjects.selectH, "10b_transaction-objects.txt", False, False, None ),
            ( "List-of-transaction-links", False, query_transactionLinks.configTransactionLinks.selectQ, ( aConfig['db-local'], vCriteriaValue, aCriteria), query_transactionLinks.configTransactionLinks.selectH, "20b_transaction-links.txt", False, False, None ),
        ]
        if aWithViolations and vLoadViolations:
            queries.extend( [
                ( "List-of-transaction-objects-with-critical-violations", False, query_transactionCriticalViolations.configTransactionObjectsWithCriticalViolations.selectQ, ( aConfig['db-local'], aConfig['db-central'], vCriteriaValue, aCriteria), query_transactionCriticalViolations.configTransactionObjectsWithCV.selectH, "30_objects-with-violations.txt", False, False, query_transactionCriticalViolations.filterTransactionObjectsWithCriticalViolation ),
                ( "List-of-transaction-objects-with-violations", False, query_transactionViolations.configTransactionObjectsWithViolations.selectQ, ( aConfig['db-local'], aConfig['db-central'], vCriteriaValue, aCriteria), query_transactionViolations.configTransactionObjectsWithViolations.selectH, "32_object-violations.txt", False, False, None ),
            ] )
        else:
            logger.warning( "Skipping CSS violation extraction cause already loaded using REST API")
        queries.extend( [
            ( "List-of-transaction-endpoints", False, query_transactionEndpoints.configTransactionEndpoints.selectQ, ( aConfig['db-local'], vCriteriaValue, aCriteria), query_transactionEndpoints.configTransactionEndpoints.selectH, "31b_transaction-endpoints.txt", False, False, None ),
            ( "List-of-obj-pro", False, query_objpros.configTransactionObjPro.selectQ, ( aConfig['db-local'], vCriteriaValue, aCriteria), query_objpros.configTransactionObjPro.selectH, "40_objects-objpro.txt", False, False, None ),
        ] )
    else:
        logger.error( "***ERROR: Wrong arguments: criteria='{0}', value='{1}', operator='{2}', skipping.".format(aCriteria,aCriteriaValue,aCriteriaOp) )
        return

    vTraceAllSqlQueries = False
    vTraceSqlQueriesOnly = False # TODO: not yet implemented
    vStopAfter = -1

    vCnxStr = postgresConnectionString(aConfig)
    logger.info( "      using connection string: {}".format(vCnxStr) )
    with psycopg2.connect(vCnxStr) as vConn:

        vWatch = common.timewatch.TimeWatch()
        vQueryNum = 0
        for iQuery in queries:
            logger.info( "        executing query: {0}...".format(iQuery[0]) )
            vWatch.start()
            vQuery = None
            if iQuery[1]:
                # query that returns a count
                vCount, vQuery = query_boilerplate.executeQueryCount2( vConn, iQuery[2], iQuery[6], vTraceAllSqlQueries or iQuery[7], *iQuery[3] )
                vWatch.stop()
                logger.info( "      -> {0}: {1}".format(iQuery[0], vCount) )
                logger.info( "      elapsed: {}, cpu: {}".format(vWatch.deltaElapsed(), vWatch.deltaCpu()) )
                aPerformances.append( ( iQuery[5], vWatch.deltaElapsed(), vWatch.deltaCpu() ))
            else:
                vFilePath = os.path.join(aOutputFolderPath,iQuery[5])
                if vDoNotOverride and os.path.isfile( vFilePath ) :
                    logger.warning( "!!!WARNING: skipping file [{}]: already generated".format(vFilePath) )
                    continue

                # query that returns a row set
                vRs, vQuery = query_boilerplate.executeQueryWithResultSet2( vConn, iQuery[2], iQuery[6], vTraceAllSqlQueries or iQuery[7], *iQuery[3] )
                vFile = None
                if iQuery[5]:
                    logger.info( "      writing to [{}]".format(vFilePath) )
                    vFile = open( vFilePath, "w")
                    # write headers
                    if iQuery[4]:
                        print( iQuery[4], file=vFile )

                vRowNum = 0
                logger.info( "      {0}:".format(iQuery[0]) )
                if vRs:
                    vFilter = iQuery[8]
                    for vRow in vRs:
                        if not vFilter or vFilter(vRow):
                            vRowNum += 1
                            vLine = '|'.join( [escapePipe(str(e)) for e in vRow] )
                            if vFile:
                                print( vLine, file=vFile )
                            else:
                                logger.info( "[Row:{:>6}]:{}".format(vRowNum,vLine) )
                                if vRowNum > 10:
                                    break
                if vFile:
                    vFile.close()
                vWatch.stop()
                logger.info( "      elapsed: {}, cpu: {}".format(vWatch.deltaElapsed(), vWatch.deltaCpu()) )
                aPerformances.append( ( iQuery[5], vWatch.deltaElapsed(), vWatch.deltaCpu() ))
            
            if  aOptions["trace-extract-css-queries"] and None!=vQuery:
                # save query in file
                with open( os.path.join(aOutputFolderPath,iQuery[5])+".sql", "w" ) as vFileQ:
                    print( vQuery, file=vFileQ )

            vQueryNum += 1
            if -1!=vStopAfter and vQueryNum>vStopAfter:
                break 

    vWatchTr.stop()
    aPerformances.append( ( "extraction-css", vWatchTr.deltaElapsed(), vWatchTr.deltaCpu() ))

