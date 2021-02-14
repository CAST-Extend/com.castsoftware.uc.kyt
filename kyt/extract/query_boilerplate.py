import collections
import logging
logger = logging.getLogger(__name__) 
logging.basicConfig(
    format='[%(levelname)-8s][%(asctime)s][%(name)-12s] %(message)s',
    level=logging.INFO
)




##== ------------------------------------------------------------------------
def postgresExecuteQuery( aConn, aQuery, aIsDDL=False, aTraceQuery=False ):
    retVal = []
    vCurs = aConn.cursor()
    #logger.info( "query:\n{}\n------".format(aQuery) )
    vRes = vCurs.execute( aQuery )
    #print( "-- begin - query ------\n{0}\n--  end  - query ------".format(aQuery), file=sys.stderr )
    if not aIsDDL:
        retVal = vCurs.fetchall()
    return retVal

#TQueryConfig = collections.namedtuple("TQueryConfig","countH countQ selectH selectQ")

##== ------------------------------------------------------------------------
# aConn : connexion
# aQuery: query that returns a count
# aArgs: arguments to use
def executeQueryCount( aConn, aQuery, aIsDDL, aTraceQuery, *aArgs):
    vFullQuery = aQuery.format( *aArgs )
    if aTraceQuery:
        logger.info( ">>>>>> QUERY:\n"+vFullQuery )
    vRs = postgresExecuteQuery( aConn, vFullQuery, aIsDDL )
    vCount = 0+vRs[0][0]
    return vCount

# Returns a tuple: ( 0: count, 1: query effectively executed )
def executeQueryCount2( aConn, aQuery, aIsDDL, aTraceQuery, *aArgs):
    vFullQuery = aQuery.format( *aArgs )
    if aTraceQuery:
        print( "[DEBUG]  -> query: {\n"+vFullQuery+"}", file=sys.stderr )
    vRs = postgresExecuteQuery( aConn, vFullQuery, aIsDDL )
    vCount = 0+vRs[0][0]
    return ( vCount, vFullQuery )


# aConn : connexion
# aQuery: query that returns a count
# aArgs: arguments to use
def executeQueryWithResultSet( aConn, aQuery, aIsDDL, aTraceQuery, *aArgs):
    vFullQuery = aQuery.format( *aArgs )
    if aTraceQuery:
        logger.info( ">>>>>> QUERY:\n"+vFullQuery )
    return postgresExecuteQuery( aConn, vFullQuery, aIsDDL )


# Returns a tuple: ( 0: result set, 1: query effectively executed )
def executeQueryWithResultSet2( aConn, aQuery, aIsDDL, aTraceQuery, *aArgs):
    vFullQuery = aQuery.format( *aArgs )
    if aTraceQuery:
        logger.info( ">>>>>> QUERY:\n"+vFullQuery )
    return ( postgresExecuteQuery( aConn, vFullQuery, aIsDDL ), vFullQuery )
