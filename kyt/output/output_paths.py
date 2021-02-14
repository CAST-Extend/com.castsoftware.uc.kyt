
import sys
import os
import json
import time
import datetime
import collections
import traceback
import logging

logger = logging.getLogger(__name__) 
logging.basicConfig(
    format='[%(levelname)-8s][%(asctime)s][%(name)-12s] %(message)s',
    level=logging.INFO
)

_CRITICAL = 0
_NON_CRITICAL = 1

# Options used
C_OPTION_GROUP_NODES_WITHOUT_VIOLATIONS="group-nodes-without-violations"

from common import timewatch
from common import config
from model import n_data
from render import gviz

TOutputer = collections.namedtuple( "TOutputer", [ "out", "prolog", "main","epilog"])
TNodeStyle=collections.namedtuple( "TNodeStyle", [ "color", "fillcolor", "shape" ])
TFontStyle=collections.namedtuple( "TFontStyle", [ "color", "fillcolor", "shape" ])

def escapeAmpLtGt( aStr ):
    return aStr.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def _outputPathNode():
    pass

# Returns: tuple
#   0: number of distincts critical violations for node
#   1: number od distincts non critical violations for node
#
def getViolationsForNode( aNode, aTransactionViolations ):
    retVal =None
    if aNode._num in aTransactionViolations and len(aTransactionViolations[int(aNode._num)])>0 :
        retVal = ( [], [] )
        vCrits = retVal[_CRITICAL]
        vNonCrits = retVal[_NON_CRITICAL]
        vLastMId = set()
        for iV in aTransactionViolations[int(aNode._num)]:
            #logger.info( "    #{}: {}: violation: {}, {}, {}".format(aNode._num,aNode._obj._object_id,
            #    iV._is_critical, iV._metric_id, iV._metric_name ) )
            if iV._metric_id not in vLastMId:
                if iV._is_critical:
                    vCrits.append( iV ) # "* {}".format(iV._metric_name) )
                else:
                    vNonCrits.append( iV ) # "  {}".format(iV._metric_name) )
                vLastMId.add( iV._metric_id )
    return retVal

# Clusterise: group node to prevent to many lines
#   to be part of current cluster a node shall
#     - have no critical violations nor non critical violations
#     - have only one successor (therefore path's end node cannot be part of a cluster)
#     - have only one predecessor (therefore path's start node cannot be part of a cluster)
def clusterisePath( aPath, aGraph, aTransactionViolations, aIsSinglePath ):
    vNewPath = []
    vNbClusters = 0
    # Computing incomings and outgoings table: taken only succ/pred in the path
    vPath = { x for x in aPath } # using set for fast lookup
    if aIsSinglePath:
        # Optim: by contruction, single pah implies 1 pres and 1 succ except for start and end nodes
        vNbIncomings = { x : 1 for x in aPath }
        vNbOutgoings = { x : 1 for x in aPath }
    else:
        vNbIncomings = { x : 0 for x in aPath }
        vNbOutgoings = { x : 0 for x in aPath }
        for iNode in aGraph._nodes:
            for iSuccNum in iNode._edges:
                if iSuccNum in vNbIncomings and iNode._num in vPath:
                    vNbIncomings[iSuccNum] += 1
        for iNodeNum in aPath:
            for iSuccNum in aGraph.edges(iNodeNum):
                if iSuccNum in vPath:
                    vNbOutgoings[iNodeNum] +=1

    vCluster = []
    for iN, iNodeNum in enumerate(aPath):
        vIsFirst = iN==0
        vIsLast = iN==len(aPath)-1
        vNode = aGraph.node(iNodeNum)

        #logger.info( "  examining node: {}: num={}, id={}, incomings={}, outgoins={}, violations={}".format(iN,iNodeNum,vNode._obj._object_id,vNbIncomings[iNodeNum],vNbOutgoings[iNodeNum],iNodeNum in aTransactionViolations) )
        if not vIsFirst and not vIsLast and 1==vNbIncomings[iNodeNum] and 1==vNbOutgoings[iNodeNum] and iNodeNum not in aTransactionViolations:
            # Good candidate to belong to a cluster
            if vCluster:
                # Already one => store it
                vCluster.append( ( vNode._num, 2, vNode._obj._object_id ) )    # 2 => part of a cluster
            else:
                # Start a cluster
        #        logger.info( "    >>>>>> starting candidate cluster: start={}".format( vNode._obj._object_id ) )
                vCluster = [ ( vNode._num, 1, vNode._obj._object_id ) ] # 1 => start of a cluster
        else:
            # Did we have a cluster ?
            if vCluster:
                # Yes => group nodes if more than 1 nodes in it
                if len(vCluster) > 1:
                    vNewPath.append( ( vCluster[0][0], 1, [ x[0] for x in vCluster[1:]] ))
                    #logger.info( "      >>>>>> created a cluster: lenght={}, start={}, end={}".format( len(vCluster), vCluster[0][2], vCluster[-1][2] ) )
                    vNbClusters += 1
                else:
        #            logger.info( "      >>>>>> dropping cluster: lenght={}, start={}, end={}".format( len(vCluster), vCluster[0][2], vCluster[-1][2] ) )
                    vNewPath.append( ( vCluster[0][0], 0 ) ) # 0 => not part of a cluster
            vCluster = []
            vNewPath.append( ( vNode._num, 0) ) # 0 -> not part of a cluster
    #logger.info( "    found clusters: {}".format(vNbClusters) )
    return vNewPath

def outputPaths( aOptions, aPathFilePath, aGVizFilePath, aGraph, aTransaction, aAllPaths, aSinglePath ):
    vObjectsInPath = set()
    #vEdgesInPath = set()
    vEdgesInPath2 = collections.OrderedDict()
    
    vWithNumAndId = False
    if 'render-num-and-object-id' in aOptions: vWithNumAndId = aOptions['render-num-and-object-id']

    
    if not aAllPaths or not aAllPaths[aTransaction._root._num] or not aAllPaths[aTransaction._root._num][0]:
        return

    with open( aPathFilePath,"w") as vFile, open(aGVizFilePath,"w") as vGvizFile:
        logger.info( "Writing path in file [{0}]...".format(aPathFilePath) )
        logger.info( "Writing graph in file [{0}]...".format(aGVizFilePath) )

        vOutputs = (
                TOutputer(vFile, _outputPathPrologPath, _outputPathNodePath, _outputPathEpilogPath),
                TOutputer(vGvizFile, _outputPathPrologGViz, _ouputPathNodeGViz, _outputPathEpilogGViz)
        )

        _outputPathProlog( vOutputs, aGraph, aTransaction, aAllPaths, aOptions )        

        vRootNode = aTransaction._root
        vWithCluster = aOptions[C_OPTION_GROUP_NODES_WITHOUT_VIOLATIONS]
        vPathNum = 0
        vRootNode = aTransaction._root
        for iPath in aAllPaths[vRootNode._num]:
            vStep = 0
            vPrevNode = None
            
            vPath = iPath[1]
            if vWithCluster:
                vClusteredPath = clusterisePath( vPath, aGraph, aTransaction._violations, aSinglePath )
                vPath = vClusteredPath

            ### Beautifier for single path
            vSameRank = []
            if aSinglePath or 1==len(aAllPaths[vRootNode._num]):
                vWithBeautify = True
                logger.info( "  applyting beauty node..."+str(len(aAllPaths)) )
                #vSinglePath = aAllPaths[vRootNode._num][0]
                vSinglePath = vPath

                #cMaxHeight = 6
                vMaxHeightOrWidth = 15
                if vWithCluster:
                    vNbNodesInPath = len(vSinglePath)
                else:
                    vNbNodesInPath = len(vSinglePath)

                if vNbNodesInPath < 6 :
                    vWithBeautify = False
                elif vNbNodesInPath < 16 :
                    vMaxHeightOrWidth = 5
                elif vNbNodesInPath < 31:
                    vMaxHeightOrWidth = 6
                elif vNbNodesInPath < 57 :
                    vMaxHeightOrWidth = 10
                else:
                    vMaxHeightOrWidth = 15

                if vWithBeautify:
                    logger.info( "  stacking max node: {}".format(vMaxHeightOrWidth) )
                    for iN, iNodeNum in enumerate(vSinglePath[::vMaxHeightOrWidth]):
                        if vWithCluster:
                            vNode = aGraph.node(iNodeNum[0])
                        else:
                            vNode = aGraph.node(iNodeNum)
                        vSameRank.append( vNode._obj._object_id )
                    print( "{{ rank = same; {} }}".format(' '.join(vSameRank)), file=vGvizFile )
            ###
            for iIdx, iElem in enumerate(vPath):
                vIsFirst = iIdx==0
                vIsLast = iIdx==len(vPath)-1
                vIsCluster = False

                if vWithCluster:
                    iNum = iElem[0]
                    vIsCluster = 1+len(iElem[2]) if iElem[1] else 0
                else:
                    iNum = iElem
                vNode = aGraph.node(iNum)

                # Prepare output for psv file
                vLine = "|{0}|{1}|{2}|{3}|{7}|{8}|{4}|{5}|{6}|".format(
                    len(aAllPaths[vRootNode._num]), vPathNum, len(vPath), vStep,                 # 0/1/2/3
                    vNode._obj._object_id, vNode._obj._object_name, vNode._obj._object_fullname, # 4/5/6
                    aTransaction._id, aTransaction._name                                                # 7/8
                )

                if iNum not in vObjectsInPath:
                    vObjectsInPath.add( iNum )
                    vObjectViolations = getViolationsForNode( vNode, aTransaction._violations )

                    # Output to text file
                    if vObjectViolations:
                        for iV in vObjectViolations[1]:
                            vLine_ = '-' + vLine + str(iV._metric_id) + '|' + iV._metric_name
                            print( vLine_, file=vFile )
                        for iCV in vObjectViolations[0]:
                            vLine_ = '*' + vLine + str(iCV._metric_id) + '|' + iCV._metric_name
                            print( vLine_, file=vFile )
                    else:
                        if vIsCluster:
                            vLine_ = 'c' + vLine + "-|-"
                        else:
                            vLine_ = ' ' + vLine + "-|-"
                        print( vLine_, file=vFile )

                    # Format node label:
                    #   cast object type
                    #   cast object name
                    #   cast critical violations if any
                    #   cast non critical violatons if any
                    #   if set in options, node num and cast object id
                    vGvizCViolations = ""
                    vGvizViolations = ""
                    vNumAndId = '<br/><font color="gray20">#{}: {}</font>'.format(vNode._num,vNode._obj._object_id) if vWithNumAndId else ""
                    
                    vNodeStyle = TNodeStyle(None,None,None)
                    if vObjectViolations and len(vObjectViolations[_NON_CRITICAL])>0:
                        # Output only 6 violations at max
                        vGvizViolations =  '<font color="{}"><br/>'.format(config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.text-color.non-crit-violation","gray")) \
                            +'<br/>'.join(escapeAmpLtGt("  {}".format(x._metric_name)) for x in vObjectViolations[_NON_CRITICAL][:6])+'</font>'
                        vNodeStyle = TNodeStyle(config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.border-color.with-non-crit","gray"),None,"box")

                    if vObjectViolations and len(vObjectViolations[_CRITICAL])>0 :
                        vGvizCViolations =  '<font color="{}"><br/>'.format(config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.text-color.crit-violation","red3")) \
                            +'<br/>'.join(escapeAmpLtGt("* {}".format(x._metric_name)) for x in vObjectViolations[_CRITICAL])+'</font>'
                        vNodeStyle = TNodeStyle(config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.border-color.with-crit","red"),None,"box")   # Warning: must be after vViolation block

                    if vIsCluster:
                        vNodeStyle = TNodeStyle(
                            config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.border-color.cluster","gray80"),
                            config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.fill-color.cluster","gray98"),
                            config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.shape.cluster","septagon")
                        )

                    if vIsCluster:
                        vClusterNodeStart = aGraph.node(iElem[1])
                        vClusterNodeEnd = aGraph.node(iElem[2][-1])
                        """
                        vGvizLabel = '<<font color="{}">{}</font><br/><font color="{}">...{}...</font><br/><font color="{}">{}</font>{}{}{}>'.format(
                            config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.text-color.cluster2","blue3"),vClusterNodeStart._obj._object_name,
                            config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.text-color.cluster","blue3"),vIsCluster-2,
                            config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.text-color.cluster2","blue3"),vClusterNodeEnd._obj._object_name,
                            vNumAndId, vGvizCViolations, vGvizViolations
                        """
                        vGvizLabel = '<<font color="{}">...{}...</font>{}>'.format(
                            config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.text-color.cluster","blue3"),vIsCluster,vNumAndId
                        )
                    else:
                        vGvizLabel = '<<u><font color="{}">{}</font></u><br/><font color="{}">{}</font>{}{}{}>'.format(
                            config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.text-color.object-type","blue3"), vNode._obj._object_type, 
                            config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.text-color.object-name","magenta3"), escapeAmpLtGt(vNode._obj._object_name),
                            vNumAndId, vGvizCViolations, vGvizViolations
                        )

                    if vIsFirst and vNode._num==aTransaction._root._num:
                        vNodeStyle = TNodeStyle(vNodeStyle.color if vNodeStyle.color else config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.border-color.entry-point","goldenrod1"),
                            config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.fill-color.entry-point","lightyellow"), "box")
                    elif vNode._num in aTransaction._endpoints:
                        vNodeStyle = TNodeStyle(vNodeStyle.color if vNodeStyle.color else config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.border-color.end-point","goldenrod1"),
                            config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.fill-color.end-point","lightyellow2"),"box")
                    
                    # Format node shape
                    vGVizNodeShape = '{}{}{} '.format(
                        'shape="{}", '.format(vNodeStyle.shape) if vNodeStyle.shape else '',
                        'color="{}", '.format(vNodeStyle.color) if vNodeStyle.color else '',
                        'fillcolor="{}"'.format(vNodeStyle.fillcolor)if vNodeStyle.fillcolor else ''
                    )

                    # Format and output node definition
                    vGvizNode = '"{}" [{}label={}];'.format(vNode._obj._object_id,vGVizNodeShape,vGvizLabel)
                    print( vGvizNode, file=vGvizFile )
                
                # Add 'real' edge: bases on how path has been constructed and not based on 'real' links as in CAST
                # To avoid too many links on the diagram
                if None != vPrevNode:
                    #vEdgesInPath.add( ( vPrevNode, vNode._num ) )
                    if vPrevNode in vEdgesInPath2:
                        vEdgesInPath2[ vPrevNode ].add( vNode._num )
                    else:
                        vEdgesInPath2[ vPrevNode ] = {vNode._num}
                vPrevNode = vNode._num
                vStep += 1

            vPathNum += 1
        
        _outputPathEpilog( vOutputs, aGraph, aTransaction, aAllPaths, aOptions, vEdgesInPath2, vSameRank )



def _outputPathProlog( aOutputs, aGrah, aTransaction, aPath, aOptions ):
    for i in aOutputs:
        i.prolog( i.out, aGrah, aTransaction, aPath, aOptions )

def _outputPathEpilog( aOutputs, aGrah, aTransaction, aPath, aOptions, aEdgesInPath, aSameRank ):
    for i in aOutputs:
        i.epilog( i.out, aGrah, aTransaction, aPath, aOptions, aEdgesInPath, aSameRank )


def _outputPathPrologPath( aOF, aGraph, aTransaction, aPaths, aOptions ):
    # output header
    for vLine in (
        "#All# 0/A: Critical | 1/B: NbPaths | 2/C: PathNum | 3/D: PathLen | 4/E: StepNum | 5/F: TransactionId | 6/G: TransactionName | 7/H: ObjectId | 8/I: ObjectName | 9/J: ObjectFullname | 10/K: MetricId | 11/L: MetricName",
        "#{{ NbPaths: {0}, TransactionId: {1}, TransactionName='{2}' }}".format(len(aPaths[aTransaction._root._num]),aTransaction._id,aTransaction._name)
    ):
        logger.debug( vLine )
        print( vLine, file=aOF )

def _outputPathNodePath( aOF, aGraph, aTransaction, aNode, aOptions ):
    pass

def _outputPathEpilogPath( aOF, aGraph, aTransaction, aPaths, aOptions, aEdgesInPath, aSameRank ):
    pass


def _outputPathPrologGViz( aOF, aGraph, aTransaction, aPaths, aOptions ):
    # Graphviz header
    print( "digraph {\n", file=aOF )
    print( '    labelloc="t"; label="{}: {}";'.format(aOptions['transaction-config']["subfolder"],aTransaction._name), file=aOF )
    print( '    rankdir=TB;', file=aOF )
    #print( '    splines=ortho', file=aOF )
    print( '    ranksep=0.35;', file=aOF )
    print( '    node [shape=none, fontname="Arial", style="filled", color="{}", fillcolor="{}"];'.format(
        config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.border-color.regular","white"),
        config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.fill-color.regular","white")
    ), file=aOF )
    print( '    graph [fontname="Arial"];', file=aOF )
    print( '    edge [fontname="Arial"];', file=aOF )

def _ouputPathNodeGViz( aOF, aGraph, aTransaction, aNode, aOptions ):
    pass

def _outputPathEpilogGViz( aOF, aGraph, aTransaction, aPath, aOptions, aEdgesInPath, aSameRank ):
    # GViz edges
    print( "\n", file=aOF )
    if aEdgesInPath:
        # Use edge set provided instead of relying on all cast links
        for iE in aEdgesInPath.keys():
            vSrce = aGraph._nodes[iE]._obj._object_id
            for iDest in aEdgesInPath[iE]:
                vDest = aGraph._nodes[iDest]._obj._object_id
                """
                if aSameRank and vDest in aSameRank:
                    print( '  edge[ weight = 1 ];', file=aOF )
                    print( '  "{0}"  -> "{1}";'.format(
                            #aGraph._nodes[iE[0]]._obj._object_id, aGraph._nodes[iE[1]]._obj._object_id ),
                            ##aGraph._nodes[iE]._obj._object_id, aGraph._nodes[aEdgesInPath[iE]]._obj._object_id ),
                            vSrce, vDest),
                            file=aOF
                    )
                    print( '  edge[ weight = 6 ];', file=aOF )
                else:
                """
                print( '  "{0}"  -> "{1}";'.format(
                        #aGraph._nodes[iE[0]]._obj._object_id, aGraph._nodes[iE[1]]._obj._object_id ),
                        ##aGraph._nodes[iE]._obj._object_id, aGraph._nodes[aEdgesInPath[iE]]._obj._object_id ),
                        vSrce, vDest),
                        file=aOF
                )
        
            # add mising nodes in grey
        """
        for iNdNum in aPath:
            for iLNum in aGraph._nodes[iNdNum]._edges:
                if iLNum in vObjectsInPath and ( iNdNum, iLNum ) not in vEdgesInPath2 :
                    print( '  "{0}"  -> "{1}" [color="gray80"];'.format(
                            aGraph._nodes[iNdNum]._obj._object_id, aGraph._nodes[iLNum]._obj._object_id ),
                            file=vGvizFile
                    )
        """
    else:
        # Show all links cast has discovered; that may increase complexity
        """
        # Output only edges for objects in path (for ease of read: not all existing edges between objects)
        print( "", file=aOF )
        for iNdNum in aPath:
            for iLNum in aGraph._nodes[iNdNum]._edges:
                if iLNum in aPath:
                    print( '  "{0}"  -> "{1}";'.format(
                        aGraph._nodes[iNdNum]._obj._object_id,aGraph._nodes[iLNum]._obj._object_id),
                        file=aOF
                    )
        print( "\n}", file=aOF )
        """
    # GViz digraph tail
    print( "\n}", file=aOF )
