import os
import sys
import collections
import psycopg2
import json
import logging
logger = logging.getLogger(__name__) 
logging.basicConfig(
    format='[%(levelname)-8s][%(asctime)s][%(name)-12s] %(message)s',
    level=logging.INFO
)

import common.timewatch
import common.config

from extract import extract_css
from extract import extract_rapi


class Acc:
    _v = None

    def sto( aExpr ):
        Acc._v = aExpr
        return Acc._v

    def v():
        retVal = Acc._v
        Acc._v = None
        return retVal


##== The main job here ------------------------------------------------------
def outputPerformances( aOptions, vQueryPerfs ):
    with open( os.path.join(aOptions['tr-output-data-folder'],"query-performances.txt"), "a+") as vF:
        print( "#0/A: Timestamp | 1/B: Subfolder | 2/C: Step | 3/D: label | 4/D: elapsed (sec) | 5/E: label | 6/F: cpu (sec)", file=vF )
        for i in vQueryPerfs:
            print( "[{}] | {} | {} | elapsed:| {} | cpu:| {}".format(
                common.timewatch.TimeWatch.generateDateTimeMSecStamp(),
                aOptions["tr-subfolder"],
                i[0],
                i[1],
                i[2]
                ), file=vF
            )


def extractTransactionData( aOptions ):
    vLogHandler = logging.FileHandler( os.path.join(aOptions["tr-output-folder"], "logs.txt") )
    vLogHandler.setLevel( logging.INFO )
    vLogHandler.setFormatter( logging.Formatter("[%(levelname)-8s][%(asctime)s][%(name)-12s] %(message)s") )
    logger.addHandler( vLogHandler )


    vQueryPerfs = []
    vWatchTr = common.timewatch.TimeWatch()

    vDoNotOverrideAll = False   # if transaction has already been dumped => return

    # extract directly from CSS
    if not vDoNotOverrideAll or not os.path.isfile( os.path.join(aOptions['tr-output-data-folder'],extract_css.C_OVERRIDEALL_EVIDENCE) ) :
        # Extract from REST API
        vRes = extract_rapi.extractTransactionData( aOptions, vQueryPerfs )
        # Extract from REST API
        extract_css.extractTransactionData( aOptions, not vRes, vQueryPerfs )

    else:
        logger.warning( "! Warning: extraction already done: keeping last results (delete files of _data folder if you want to extract again)")


    vWatchTr.stop()
    vQueryPerfs.append( ( "extraction", vWatchTr.deltaElapsed(), vWatchTr.deltaCpu() ))
    outputPerformances( aOptions, vQueryPerfs )

    ### VERIFICATION: consistency between css and rest api
    vDiff = {
        "CSS"   : { "nbLines":0, "v":set(), "o":set(), "path": os.path.join(aOptions['tr-output-data-folder'], "30_objects-with-violations.txt") },
        "RAPI"  : { "nbLines":0, "v":set(), "o":set(), "path": os.path.join(aOptions['tr-output-data-folder'], "30_objects-with-violations2.txt") }
    }
    for i in vDiff.keys():
        if os.path.isfile(vDiff[i]["path"]):
            with open( vDiff[i]["path"], "r" ) as vIF:
                for iLine in vIF:
                    if '#' != iLine[0]:
                        vDiff[i]["nbLines"] += 1
                        vLine = iLine.strip().split('|')
                        vDiff[i]["o"].add( vLine[2] )
                        vDiff[i]["v"].add( vLine[2] + ':' + vLine[6] + ':' + vLine[10] )

    for i in vDiff:
        logger.info( "{}: nbLines={}, nbObjects={}, nbViolations={}".format(i,vDiff[i]["nbLines"],len(vDiff[i]["o"]), len(vDiff[i]["v"])))
    logger.info( "" )
    logger.removeHandler( vLogHandler )


def kytExtractMain( aArgv ):

    if 0==len(aArgv) or not os.path.isfile( aArgv[0] ):
        logger.error( "***ERROR: No valid configuration file, exiting." )
        return 1

    vConfiguration = common.config.CConfig(aArgv[0])

    vConfiguration.processConfigurations(extractTransactionData,None,False)
    return 0


if __name__ == "__main__":
    logger.info( "Starting..." )
    vWatch = common.timewatch.TimeWatch()
    kytExtractMain( sys.argv[1:] )
    vWatch.stop()
    logger.info( "Finished: elapsed: {}, cpu: {}".format(vWatch.deltaElapsed(),vWatch.deltaCpu()) )