from extract import query



##== Transaction objects with critical violations ---------------------------
queryTransactionObjectsWithCV_byX_base_DEPRECATED="""\
SELECT DISTINCT
    L2C.site_object_id     AS "LocalObjectId",
    O.object_id            AS "Central0bjectId",
    R.metric_id-1          AS "MetricId",
    -- critical
    CASE WHEN (
        SELECT MAX(sT.metric_critical)
        FROM   {1}.dss_metric_histo_tree sT
        WHERE  sT.metric_id=R.metric_id-1 AND sT.snapshot_id=R.snapshot_id
    ) = 1 THEN 'Yes'
          ELSE 'No'
    END                    AS "Critical",
    Q.b_criterion_id,
    Q.t_criterion_id,
    O.object_name          AS "ObjectName",
    O.object_full_name     AS "ObjectFullname",
    Q.b_criterion_name,
    Q.t_criterion_name,
    Q.metric_name          AS "MetricName",
    --
    R.snapshot_id          AS "SnapshotId", 
    O.object_description   AS "ObjectDescription"
FROM
    -- Objects of transaction -> LOCAL_O
    {0}.cdt_objects                OT
    JOIN {0}.dss_transaction       T	   ON T.form_id = OT.object_id
    JOIN {0}.dss_objects           OT2     ON OT2.object_id = T.object_id
    JOIN {0}.dss_links             L       ON L.previous_object_id = OT2.object_id
    JOIN {0}.cdt_objects           LOCAL_O ON LOCAL_O.object_id = L.next_object_id	
    --
    -- translate local object ids into central object ids
    JOIN {1}.dss_translation_table L2C	   ON L2C.site_object_id = LOCAL_O.object_id
    JOIN {1}.dss_metric_results    R	   ON R.object_id = L2C.object_id
    -- for information to be output in select part
    JOIN {1}.dss_objects           O	   ON O.object_id=L2C.object_id
    JOIN {1}.csv_quality_tree      Q	   ON Q.metric_id=R.metric_id-1
WHERE 1=1
    -- objects in transaction
    AND OT.object_{3} = {2}
    AND OT2.object_type_id = 30002		
    --
    AND R.snapshot_id = ( SELECT MAX(S.snapshot_id) FROM {1}.dss_snapshots S )
    --
    AND R.metric_value_index=1
    AND Q.b_criterion_id = 60017
    AND 1=(
        SELECT MAX(iT.metric_critical)
        FROM   {1}.dss_metric_histo_tree iT
        WHERE  iT.metric_id=R.metric_id-1 AND iT.snapshot_id=R.snapshot_id
    )
"""

queryTransactionObjectsWithCV_byX_base="""\
SELECT DISTINCT
    L2C.site_object_id     AS "LocalObjectId",
    O.object_id            AS "Central0bjectId",
    R.metric_id-1          AS "MetricId",
    -- critical
    CASE WHEN (
        SELECT MAX(sT.metric_critical)
        FROM   {1}.dss_metric_histo_tree sT
        WHERE  sT.metric_id=R.metric_id-1 AND sT.snapshot_id=R.snapshot_id
    ) = 1 THEN 'Yes'
          ELSE 'No'
    END                    AS "Critical",
    Q.b_criterion_id,
    Q.t_criterion_id,
    O.object_name          AS "ObjectName",
    O.object_full_name     AS "ObjectFullname",
    Q.b_criterion_name,
    Q.t_criterion_name,
    Q.metric_name          AS "MetricName",
    --
    R.snapshot_id          AS "SnapshotId", 
    O.object_description   AS "ObjectDescription"
FROM
    -- Objects of transaction -> LOCAL_O
    {0}.cdt_objects                OT
    JOIN {0}.dss_transaction       T	   ON T.form_id = OT.object_id
    JOIN {0}.dss_objects           OT2     ON OT2.object_id = T.object_id
    JOIN {0}.dss_links             L       ON L.previous_object_id = OT2.object_id
    JOIN {0}.cdt_objects           LOCAL_O ON LOCAL_O.object_id = L.next_object_id	
    --
    -- translate local object ids into central object ids
    JOIN {1}.dss_translation_table L2C	   ON L2C.site_object_id = LOCAL_O.object_id
    JOIN {1}.dss_metric_results    R	   ON R.object_id = L2C.object_id
    -- for information to be output in select part
    JOIN {1}.dss_objects           O	   ON O.object_id=L2C.object_id
    JOIN {1}.csv_quality_tree      Q	   ON Q.metric_id=R.metric_id-1
	JOIN {1}.dss_metric_histo_tree	HT	ON HT.metric_id=R.metric_id-1
													AND HT.snapshot_id=LOCAL_O.snapshot_id
WHERE 1=1
    -- objects in transaction
    AND OT.object_{3} = {2}
    AND OT2.object_type_id = 30002		
    --
    AND R.snapshot_id = ( SELECT MAX(S.snapshot_id) FROM {1}.dss_snapshots S )
    --
    AND R.metric_value_index=1
    AND Q.b_criterion_id = 60017
    AND 1=HT.metric_critical
    --AND 1=(
    --    SELECT MAX(iT.metric_critical)
    --    FROM   {1}.dss_metric_histo_tree iT
    --    WHERE  iT.metric_id=R.metric_id-1 AND iT.snapshot_id=R.snapshot_id
    --)
"""
configTransactionObjectsWithCV=query.TQueryConfig(
	countH	= "#NbOfTransactionObjectsWithVC",
	countQ	= """SELECT COUNT(0) FROM (
-- -- -- begin -- -- --
--
"""+queryTransactionObjectsWithCV_byX_base+"""--
-- -- -- end -- -- --
) AS InnerQuery
""",
	selectH	= "#LocalObjectId|CentralObjectId|MetricId|isCritical|"\
    	"BCriterionId|TCriterionId|ObjectName|ObjectFullname|BCriterionName|TCriterionName|MetricName|"\
    	"SnapshotId|ObjectDesc",
	selectQ	= queryTransactionObjectsWithCV_byX_base
)


### Version with temporary table
queryTransactionObjectsWithCriticalViolations_byX_base_DEPRECATED="""\
CREATE TEMPORARY TABLE temp_object_ids (
  object_id int4, object_name varchar(1000), object_fullname varchar(1000), object_central_id int4,
  object1_id int4, object1_name varchar(1000), object1_fullname varchar(1000),
  object2_id int4, object2_name varchar(1000), object2_fullname varchar(1000),
  valstr varchar(255), valint int4,
  val1str varchar(255), val1int int4,
  val2str varchar(255), val2int int4,
  snapshot_id int4
)
;
INSERT INTO temp_object_ids
SELECT
    OA.object_id       "ObjectId",				-- -> object_id
    OA.object_name     "ObjectName",			-- -> object_name
    OA.object_fullname	"ObjectFullname",		-- -> object_fullname
    L2C.object_id,										-- -> object_central_id
    --
    OT.object_id		"TransactionId",				-- -> object1_id
    OT.object_name     "TransactionName",				-- -> object1_name
    OT.object_fullname	"TransactionFullname",			-- -> object1_fullname
    --
    NULL, NULL,	NULL,								-- -> object_id, object2_name, object_fullname								
    OT.object_type_str "TransactionType", NULL,		-- -> valstr, valint
    OA.object_type_Str "ArtifactType", NULL,		-- -> val1str, val1int
    'Transaction-object' 	"EntryKind", NULL,			-- -> val2str, val2int
    NULL											-- -> sanpshot_id
FROM
    {0}.cdt_objects				OT
    JOIN {0}.dss_transaction	TR	ON TR.form_id = OT.object_id
    JOIN {0}.dss_objects		OT2	ON OT2.object_id = TR.object_id
    JOIN {0}.dss_links			L ON L.previous_object_id = OT2.object_id
    JOIN {0}.cdt_objects 		OA	ON OA.object_id = L.next_object_id
    --
    JOIN {1}.dss_translation_table	L2C	ON L2C.site_object_id = OA.object_id
WHERE 1=1
    AND OT.object_{3} = {2}
    AND OT2.object_type_id = 30002
;
UPDATE temp_object_ids AS ttemp SET snapshot_id = ( SELECT MAX(S.snapshot_id) FROM {1}.dss_snapshots S )
;
SELECT DISTINCT
    LOCAL_O.object_id		AS "LocalObjectId", -- 0
    LOCAL_O.object_central_id			AS "Central0bjectId", -- 1
    R.metric_id-1 AS "MetricId", -- 2
-- critical 
CASE	WHEN (
SELECT	MAX(sT.metric_critical)
FROM		{1}.dss_metric_histo_tree sT
WHERE 	sT.metric_id=R.metric_id-1 AND sT.snapshot_id=R.snapshot_id
) = 1	THEN 'Yes'
ELSE		'No'
END AS "Critical", -- 3
QB.metric_id, --4 -- Q.b_criterion_id,
QT.metric_id, --5 -- Q.t_criterion_id,
O.object_name			AS "ObjectName", -- 6
O.object_full_name		AS "ObjectFullname", -- 7
QB.metric_name, QT.metric_name, --8, 9 -- Q.b_criterion_name, Q.t_criterion_name,
Q.metric_name AS "MetricName", -- 10
--
R.snapshot_id AS "SnapshotId", -- 11
O.object_description	AS "ObjectDescription", -- 12
--
R.metric_value_index AS "MetricValueIndex", -- 13
Q.metric_group AS "MetricGroup" --14
FROM
    -- Objects of transaction -> LOCAL_O
    temp_object_ids LOCAL_O
    --
    -- translate local object ids into central object ids
    JOIN {1}.dss_metric_results		R	ON R.object_id = LOCAL_O.object_central_id AND R.snapshot_id+0=LOCAL_O.snapshot_id
    -- for information to be output in select part
    JOIN {1}.dss_metric_types		Q	ON Q.metric_id=R.metric_id-1
	JOIN {1}.dss_metric_type_trees	M2T ON M2T.metric_id=Q.metric_id
	JOIN {1}.dss_metric_types		QT	ON QT.metric_id=M2T.metric_parent_id
	JOIN {1}.dss_metric_type_trees	T2B ON T2B.metric_id=QT.metric_id
	JOIN {1}.dss_metric_types		QB	ON QB.metric_id=T2B.metric_parent_id
    --
    JOIN {1}.dss_objects			O	ON O.object_id=LOCAL_O.object_central_id
	JOIN {1}.dss_metric_histo_tree	HT	ON HT.metric_id=R.metric_id-1
													AND HT.snapshot_id+0=R.snapshot_id
WHERE 1=1
    --AND R.metric_value_index =1 -- 32 sec
	--AND Q.metric_group+0 IN ( 1, 5, 15 ) -- 15 sec
	AND QT.metric_group = 13
	AND QB.metric_group = 10
    AND QB.metric_id = 60017	-- b_criterion_id
    AND 1=HT.metric_critical
"""
queryTransactionObjectsWithCriticalViolations_byX_base="""\
CREATE TEMPORARY TABLE temp_object_ids (
  object_id int4, object_name varchar(1000), object_fullname varchar(1000), object_central_id int4,
  object1_id int4, object1_name varchar(1000), object1_fullname varchar(1000),
  object2_id int4, object2_name varchar(1000), object2_fullname varchar(1000),
  valstr varchar(255), valint int4,
  val1str varchar(255), val1int int4,
  val2str varchar(255), val2int int4,
  snapshot_id int4
)
;
INSERT INTO temp_object_ids
SELECT
    OA.object_id       "ObjectId",				-- -> object_id
    OA.object_name     "ObjectName",			-- -> object_name
    OA.object_fullname	"ObjectFullname",		-- -> object_fullname
    L2C.object_id,										-- -> object_central_id
    --
    OT.object_id		"TransactionId",				-- -> object1_id
    OT.object_name     "TransactionName",				-- -> object1_name
    OT.object_fullname	"TransactionFullname",			-- -> object1_fullname
    --
    NULL, NULL,	NULL,								-- -> object_id, object2_name, object_fullname								
    OT.object_type_str "TransactionType", NULL,		-- -> valstr, valint
    OA.object_type_Str "ArtifactType", NULL,		-- -> val1str, val1int
    'Transaction-object' 	"EntryKind", NULL,			-- -> val2str, val2int
    NULL											-- -> sanpshot_id
FROM
    {0}.cdt_objects				OT
    JOIN {0}.dss_transaction	TR	ON TR.form_id = OT.object_id
    JOIN {0}.dss_objects		OT2	ON OT2.object_id = TR.object_id
    --
    -- --JOIN {0}.dss_links			L ON L.previous_object_id = OT2.object_id
    -- --JOIN {0}.cdt_objects 		OA	ON OA.object_id = L.next_object_id
    JOIN {0}.dss_transactiondetails		DT	ON DT.object_id = OT2.object_id
    JOIN {0}.cdt_objects 		OA	ON OA.object_id = DT.child_id
    --
    JOIN {1}.dss_translation_table	L2C	ON L2C.site_object_id = OA.object_id
WHERE 1=1
    AND OT.object_{3} = {2}
    AND OT2.object_type_id = 30002
;
UPDATE temp_object_ids AS ttemp SET snapshot_id = ( SELECT MAX(S.snapshot_id) FROM {1}.dss_snapshots S )
;
SELECT DISTINCT
    LOCAL_O.object_id		AS "LocalObjectId", -- 0
    LOCAL_O.object_central_id			AS "Central0bjectId", --1
    R.metric_id-1 AS "MetricId", -- 2
-- critical
    'Yes' AS "Critical", --3
QB.metric_id, -- 4 -- Q.b_criterion_id,
QT.metric_id, -- 5 -- Q.t_criterion_id,
O.object_name			AS "ObjectName", -- 6
O.object_full_name		AS "ObjectFullname", -- 7
QB.metric_name, QT.metric_name, -- 8, 9 -- Q.b_criterion_name, Q.t_criterion_name,
Q.metric_name AS "MetricName", -- 10
--
R.snapshot_id AS "SnapshotId", -- 11
O.object_description	AS "ObjectDescription", -- 12
--
R.metric_value_index AS "MetricValueIndex", -- 13
Q.metric_group AS "MetricGroup" -- 14
FROM
    -- Objects of transaction -> LOCAL_O
	    temp_object_ids LOCAL_O
    JOIN {1}.dss_metric_results		R	ON R.object_id = LOCAL_O.object_central_id AND R.snapshot_id=LOCAL_O.snapshot_id
    -- for information to be output in select part
    JOIN {1}.dss_metric_types		Q	ON Q.metric_id=R.metric_id-1
	JOIN {1}.dss_metric_type_trees	M2T ON M2T.metric_id=Q.metric_id
	JOIN {1}.dss_metric_types		QT	ON QT.metric_id=M2T.metric_parent_id
	JOIN {1}.dss_metric_type_trees	T2B ON T2B.metric_id=QT.metric_id
	JOIN {1}.dss_metric_types		QB	ON QB.metric_id=T2B.metric_parent_id
--x---JOIN newtron_cms_central.csv_quality_tree		Q	ON Q.metric_id=R.metric_id-1
    JOIN {1}.dss_objects			O	ON O.object_id=LOCAL_O.object_central_id
	JOIN {1}.dss_metric_histo_tree	HT	ON HT.metric_id=R.metric_id-1
													AND HT.snapshot_id=R.snapshot_id
WHERE 1=1
    --AND R.metric_value_index IN ( 1, 1 ) -- 32 sec
	--AND Q.metric_group+0 IN ( 1, 5, 15 ) -- 15 sec
	AND QT.metric_group = 13
	AND QB.metric_group = 10
    AND QB.metric_id = 60017	-- b_criterion_id
    AND 1=HT.metric_critical
"""

# Pity: filter required in py cause adding where/jon clause breaks the performance
def filterTransactionObjectsWithCriticalViolation( aRow ):
    retVal=True # by default keep the row
    if int(aRow[13])!=1 or int(aRow[14]) not in (1, 5, 15):
        retVal = False
    return retVal


configTransactionObjectsWithCriticalViolations=query.TQueryConfig(
	countH	= "#NbOfTransactionObjectsWithVC",
	countQ	= """SELECT COUNT(0) FROM (
-- -- -- begin -- -- --
--
"""+queryTransactionObjectsWithCV_byX_base+"""--
-- -- -- end -- -- --
) AS InnerQuery
""",
	selectH	= "#LocalObjectId|CentralObjectId|MetricId|isCritical|"\
    	"BCriterionId|TCriterionId|ObjectName|ObjectFullname|BCriterionName|TCriterionName|MetricName|"\
    	"SnapshotId|ObjectDesc",
	selectQ	= queryTransactionObjectsWithCriticalViolations_byX_base
)