
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
def getViolationsForNode( aNode ):
   retVal = None
    if aNode._num in aTransaction._violations and len(aTransaction._violations[int(aNode._num)])>0 :
        vCViolations = []
        vViolations = []
        vLastMId = set()
        for iV in aTransaction._violations[int(aNode._num)]:
            #logger.info( "    #{}: {}: violation: {}, {}, {}".format(aNode._num,aNode._obj._object_id,
            #    iO._is_critical, iO._metric_id, iO._metric_name ) )
            if iV._metric_id not in vLastMId:
                if iV._is_critical:
                    vLine_ = '*' + vLine + str(iO._metric_id) + '|' + iO._metric_name
                    vCViolations.append( "* {}".format(iO._metric_name) )
                else:
                    vLine_ = '-' + vLine + str(iO._metric_id) + '|' + iO._metric_name
                    vViolations.append( "  {}".format(iO._metric_name) )
                print( vLine_, file=vFile )
                vLastMId.add( iO._metric_id )

    else:
        vLine_ = ' ' + vLine + "-|-"
        print( vLine_, file=vFile )
    return retVal


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
        
        ###
        vSameRank = []
        vWithBeautify = False
        if aSinglePath or 1==len(aAllPaths[vRootNode._num]):
            logger.info( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> "+str(len(aAllPaths)) )
            vPath = aAllPaths[vRootNode._num][0]
            
            #cMaxHeight = 6
            cMaxHeight = 15
            for iN, iNodeNum in enumerate(vPath[1][::cMaxHeight]):
                vNode = aGraph.node(iNodeNum)
                vSameRank.append( vNode._obj._object_id )
            print( "{{ rank = same; {} }}".format(' '.join(vSameRank)), file=vGvizFile )
            vWithBeautify = True
        ###
        vPath = 0
        vRootNode = aTransaction._root
        for iPath in aAllPaths[vRootNode._num]:
            vStep = 0
            vPrevNode = None
            for iIdx, iNum in enumerate(iPath[1]):
                vIsFirst = iIdx==0
                vIsLast = iIdx==len(iPath[1])-1
                vNode = aGraph.node(iNum)

                # Output for psv file
                vLine = "|{0}|{1}|{2}|{3}|{7}|{8}|{4}|{5}|{6}|".format(
                    len(aAllPaths[vRootNode._num]), vPath, len(iPath[1]), vStep,                 # 0/1/2/3
                    vNode._obj._object_id, vNode._obj._object_name, vNode._obj._object_fullname, # 4/5/6
                    aTransaction._id, aTransaction._name                                                # 7/8
                )

                vCluster = []
                if iNum not in vObjectsInPath:
                    vObjectsInPath.add( iNum )
                    vViolations = getViolationsForNode( vNode )
                    #logger.debug("  examining: {}: {}".format(vNode._obj._object_id,vLine) )
                    vCViolations = []
                    vViolations = []
                    if vNode._num in aTransaction._violations and len(aTransaction._violations[int(vNode._num)])>0 :
                        vLastMId = set()
                        #logger.debug("  -> {}: {}".format(len(vObjWithV),vObjWithV) )
                        vObjWithV = aTransaction._violations[int(vNode._num)]
                        for iO in vObjWithV:
                            #logger.info( "    #{}: {}: violation: {}, {}, {}".format(vNode._num,vNode._obj._object_id,
                            #    iO._is_critical, iO._metric_id, iO._metric_name ) )
                            if iO._metric_id not in vLastMId:
                                if iO._is_critical:
                                    vLine_ = '*' + vLine + str(iO._metric_id) + '|' + iO._metric_name
                                    vCViolations.append( "* {}".format(iO._metric_name) )
                                else:
                                    vLine_ = '-' + vLine + str(iO._metric_id) + '|' + iO._metric_name
                                    vViolations.append( "  {}".format(iO._metric_name) )
                                logger.debug( vLine_ )
                                print( vLine_, file=vFile )
                                vLastMId.add( iO._metric_id )
                                logger.debug( "  outputing node: {}: {}".format(vNode._obj._object_id,vLine) )

                    else:
                        vLine_ = ' ' + vLine + "-|-"
                        logger.debug( vLine_ )
                        print( vLine_, file=vFile )

                    # Output to text file
                    if vViolations:
                    else:
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
                    if len(vViolations)>0:
                        # Output only 6 violations at max
                        vGvizViolations =  '<font color="{}"><br/>'.format(config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.text-color.non-crit-violation","gray")) \
                            +'<br/>'.join(escapeAmpLtGt(str(x)) for x in vViolations[:6])+'</font>'
                        vNodeStyle = TNodeStyle(config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.border-color.with-non-crit","gray"),None,"box")

                    if len(vCViolations)>0 :
                        vGvizCViolations =  '<font color="{}"><br/>'.format(config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.text-color.crit-violation","red3")) \
                            +'<br/>'.join(escapeAmpLtGt(str(x)) for x in vCViolations)+'</font>'
                        vNodeStyle = TNodeStyle(config.CConfigUtil.getOptionFromOPath(aOptions,"style.node.border-color.with-crit","red"),None,"box")   # Warning: must be after vViolation block

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
                
                # Add 'real' edge
                if None != vPrevNode:
                    #vEdgesInPath.add( ( vPrevNode, vNode._num ) )
                    if vPrevNode in vEdgesInPath2:
                        vEdgesInPath2[ vPrevNode ].add( vNode._num )
                    else:
                        vEdgesInPath2[ vPrevNode ] = {vNode._num}
                vPrevNode = vNode._num
                vStep += 1

            vPath += 1
        
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
    #print( '    rankdir=TB;', file=aOF )
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
    # GViz edges
    """
    if aSameRank:
        print( '  edge[ weigth = 6 ];', file=aOF )
    """
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
    for iNdNum in vObjectsInPath:
        for iLNum in aGraph._nodes[iNdNum]._edges:
            if iLNum in vObjectsInPath and ( iNdNum, iLNum ) not in vEdgesInPath :
                print( '  "{0}"  -> "{1}" [color="gray80"];'.format(
                        aGraph._nodes[iNdNum]._obj._object_id, aGraph._nodes[iLNum]._obj._object_id ),
                        file=vGvizFile
                )
    """

    # GViz digraph tail
    print( "\n}", file=aOF )
