from extract import query

##== Transaction objects with all violation details -------------------------
# {0}: local schema name, {1}: central schema, {2}: transaction name/transaction fullname
# Result set: { "LocalObject", "TransactionName", "RootId", "RootName", "RootFullname", "RootType" }
queryTransactionObjectsWithV_byX_base="""\
--
-- TQI: 60017, Robustness: 60013, Efficiency: 60014, Security: 60016, Changeability: 60012, Transferability: 60011
-- Others: Architectural Design: 66032, Documentation: 66033, Programming Practices: 66031,
--  SEI Maintainability: 60015
-- 
SELECT
	LOCAL_O.object_id AS "ObjectId(Local)", LOCAL_O.object_name AS "ObjectName", O.object_id AS "ObjectId(Central)",
	Q.metric_id AS "MetricId", Q.metric_name AS "MetricName", 
	Q.b_criterion_id AS "BCriterionId", Q.b_criterion_name AS "BCriterionName",
	Q.t_criterion_id AS "TCriterionId", Q.t_criterion_name AS "TCriterionName",
	Q.t_weight AS "TWeight", Q.m_weight AS "MWeight", Q.t_crit AS "TCrit", Q.m_crit AS "MCrit",
	LOCAL_O.transaction_id AS "TransactionId", LOCAL_O.transaction_name AS "TransactionName",
	LOCAL_O.object_fullname AS "ObjectFullname", LOCAL_O.transaction_fullname AS "TransactionFullname"
FROM
	(
		SELECT
		    iO.object_id AS "object_id", iO.object_name AS "object_name",
		    iO.object_fullname AS "object_fullname", iO.object_type_str AS "object_type_str",
		    iOT.object_id AS "transaction_id", iOT.object_name AS "transaction_name",
		    iOT.object_fullname AS "transaction_fullname", iOT.object_type_str AS "transaction_type_str"	
		FROM
			{0}.cdt_objects			iOT
			JOIN {0}.dss_transaction	iT	ON iT.form_id = iOT.object_id
			JOIN {0}.dss_objects		iOT2	ON iOT2.object_id = iT.object_id
			JOIN {0}.dss_links		iTL	ON iTL.previous_object_id = iOT2.object_id
			JOIN {0}.cdt_objects		iO	ON iO.object_id = iTL.next_object_id
		WHERE 1=1
    		AND iOT.object_{3} = {2}
			AND iOT2.object_type_id = 30002
	) AS LOCAL_O
	-- translate local object ids into central object ids
	JOIN {1}.dss_translation_table		L2C	ON L2C.site_object_id = LOCAL_O.object_id
	JOIN {1}.dss_metric_results		R	ON R.object_id = L2C.object_id
	-- for information to be output in select part
	JOIN {1}.dss_objects				O	ON O.object_id=L2C.object_id
	JOIN {1}.csv_quality_tree			Q	ON Q.metric_id=R.metric_id-1
WHERE 1=1
	AND R.metric_value_index=1
	AND Q.b_criterion_id IN ( 60017, 60013, 60014, 60016, 60012, 60011 )
ORDER BY
	LOCAL_O.transaction_id, LOCAL_O.object_id, Q.metric_id, Q.b_criterion_name, Q.t_criterion_name  
"""

configTransactionObjectsWithV=query.TQueryConfig(
	countH	= "#NbOfTransactionViolations",
	countQ	= """SELECT COUNT(0) FROM (
-- -- -- begin -- -- --
--
"""+queryTransactionObjectsWithV_byX_base+"""--
-- -- -- end -- -- --
) AS InnerQuery
""",
	selectH	= "#0/A:LocalObjectId|1/B:ObjectName|2/C:CentralObjectId|"\
	"3/D:MetricId|4/E:MetricName|"\
    "5/F:BCriterionId|6/G:BCriterionName|7/H:TCriterionId|8/I:TCriterionName|"\
	"9/J:TWeight|10/K:MWeight|11/L:TCrit|12/M:MCrit|"\
	"13/N:TransactionId|14/O:TransactionName|"\
	"15/P:ObjectFullname|16/Q:TransactionFullname",
	selectQ	= queryTransactionObjectsWithV_byX_base
)


## Version with temporary table
# {0}: local schema name, {1}: central schema, {2}: transaction name/transaction fullname
# Result set: { "LocalObject", "TransactionName", "RootId", "RootName", "RootFullname", "RootType" }
queryTransactionObjectsWithViolations_byX_base_DEPRECATED="""\
CREATE TEMPORARY TABLE temp_object_ids2 (
    object_id int4, object_name varchar(1000), object_fullname varchar(1000),
    object_central_id int4,
    transaction_id int4, transaction_name varchar(1000), transaction_fullname varchar(1000),
    transaction_type varchar(255),
    object_type_str varchar(255),
    entry_kind varchar(255),
	snapshot_id int4
)
;
INSERT INTO temp_object_ids2
SELECT
    OA.object_id       "ObjectId",				-- -> object_id
    OA.object_name     "ObjectName",			-- -> object_name
    OA.object_fullname	"ObjectFullname",		-- -> object_fullname
	L2C.object_id,										-- -> object_central_id
	--
	OT.object_id        "TransactionId",				-- -> transaction_id
    OT.object_name      "TransactionName",				-- -> transaction_name
    OT.object_fullname  "TransactionFullname",			-- -> transaction_fullname
	--					
    OT.object_type_str  "TransactionType",		-- -> transaction_type
    OA.object_type_Str  "ArtifactType",			-- -> object_type_str
    'Transaction-object' 	"EntryKind",		-- -> entry_kind
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
UPDATE temp_object_ids2 AS ttemp SET snapshot_id = ( SELECT MAX(S.snapshot_id) FROM {1}.dss_snapshots S )
;
SELECT
	LOCAL_O.object_id AS "ObjectId(Local)", LOCAL_O.object_name AS "ObjectName",
	O.object_id AS "ObjectId(Central)",
	Q.metric_id AS "MetricId", Q.metric_name AS "MetricName", 
	Q.b_criterion_id AS "BCriterionId", Q.b_criterion_name AS "BCriterionName",
	Q.t_criterion_id AS "TCriterionId", Q.t_criterion_name AS "TCriterionName",
	Q.t_weight AS "TWeight", Q.m_weight AS "MWeight", Q.t_crit AS "TCrit", Q.m_crit AS "MCrit",
	LOCAL_O.transaction_id AS "TransactionId", LOCAL_O.transaction_name AS "TransactionName",
	LOCAL_O.object_fullname AS "ObjectFullname", LOCAL_O.transaction_fullname AS "TransactionFullname",
	R.snapshot_id AS "SnapshotId"
FROM
	temp_object_ids2             LOCAL_O
	JOIN {1}.dss_metric_results R   ON R.object_id = LOCAL_O.object_central_id and R.snapshot_id=LOCAL_O.snapshot_id
	JOIN {1}.dss_objects        O   ON O.object_id=LOCAL_O.object_central_id
	JOIN {1}.csv_quality_tree   Q   ON Q.metric_id=R.metric_id-1
WHERE 1=1
	AND R.metric_value_index=1
	AND Q.b_criterion_id IN ( 60017, 60013, 60014, 60016, 60012, 60011 )
ORDER BY
	LOCAL_O.transaction_id, LOCAL_O.object_id, Q.metric_name, Q.b_criterion_name, Q.t_criterion_name  
"""

queryTransactionObjectsWithViolations_byX_base="""\
CREATE TEMPORARY TABLE temp_object_ids2 (
    object_id int4, object_name varchar(1000), object_fullname varchar(1000),
    object_central_id int4,
    transaction_id int4, transaction_name varchar(1000), transaction_fullname varchar(1000),
    transaction_type varchar(255),
    object_type_str varchar(255),
    entry_kind varchar(255),
	snapshot_id int4
)
;
INSERT INTO temp_object_ids2
SELECT
    OA.object_id       "ObjectId",				-- -> object_id
    OA.object_name     "ObjectName",			-- -> object_name
    OA.object_fullname	"ObjectFullname",		-- -> object_fullname
	L2C.object_id,										-- -> object_central_id
	--
	OT.object_id        "TransactionId",				-- -> transaction_id
    OT.object_name      "TransactionName",				-- -> transaction_name
    OT.object_fullname  "TransactionFullname",			-- -> transaction_fullname
	--					
    OT.object_type_str  "TransactionType",		-- -> transaction_type
    OA.object_type_Str  "ArtifactType",			-- -> object_type_str
    'Transaction-object' 	"EntryKind",		-- -> entry_kind
	NULL											-- -> sanpshot_id
FROM
    {0}.cdt_objects				OT
    JOIN {0}.dss_transaction	TR	ON TR.form_id = OT.object_id
	JOIN {0}.dss_objects		OT2	ON OT2.object_id = TR.object_id
	-- --JOIN {0}.dss_links			L ON L.previous_object_id = OT2.object_id
    -- --JOIN {0}.cdt_objects 		OA	ON OA.object_id = L.next_object_id
	JOIN {0}.dss_transactiondetails		DT	ON DT.object_id = OT2.object_id
	JOIN {0}.cdt_objects		OA	ON OA.object_id = DT.child_id
	--
	JOIN {1}.dss_translation_table	L2C	ON L2C.site_object_id = OA.object_id
WHERE 1=1
	AND OT.object_{3} = {2}
    AND OT2.object_type_id = 30002
;
UPDATE temp_object_ids2 AS ttemp SET snapshot_id = ( SELECT MAX(S.snapshot_id) FROM {1}.dss_snapshots S )
;
SELECT
	LOCAL_O.object_id AS "ObjectId(Local)", LOCAL_O.object_name AS "ObjectName",
	O.object_id AS "ObjectId(Central)",
	Q.metric_id AS "MetricId", Q.metric_name AS "MetricName", 
	QB.metric_id AS "BCriterionId", QB.metric_name AS "BCriterionName",
	QT.metric_id AS "TCriterionId", QT.metric_name AS "TCriterionName",
	M2T.aggregate_weight AS "TWeight", T2B.aggregate_weight AS "MWeight",
	T2B.metric_critical AS "TCrit", M2T.metric_critical AS "MCrit",
	LOCAL_O.transaction_id AS "TransactionId", LOCAL_O.transaction_name AS "TransactionName",
	LOCAL_O.object_fullname AS "ObjectFullname", LOCAL_O.transaction_fullname AS "TransactionFullname",
	R.snapshot_id AS "SnapshotId"
FROM
	temp_object_ids2             LOCAL_O
    JOIN {1}.dss_metric_results		R	ON R.object_id = LOCAL_O.object_central_id
													AND R.snapshot_id+0=LOCAL_O.snapshot_id
	JOIN {1}.dss_objects        O   ON O.object_id=LOCAL_O.object_central_id
    JOIN {1}.dss_metric_types		Q	ON Q.metric_id=R.metric_id-1
	JOIN {1}.dss_metric_type_trees	M2T ON M2T.metric_id=Q.metric_id
	JOIN {1}.dss_metric_types		QT	ON QT.metric_id=M2T.metric_parent_id
	JOIN {1}.dss_metric_type_trees	T2B ON T2B.metric_id=QT.metric_id
	JOIN {1}.dss_metric_types		QB	ON QB.metric_id=T2B.metric_parent_id
WHERE 1=1
	AND R.metric_value_index=1
	AND QB.metric_id IN ( 60017, 60013, 60014, 60016, 60012, 60011 )
ORDER BY
	LOCAL_O.transaction_id, LOCAL_O.object_id, Q.metric_name, QB.metric_id, QT.metric_id"""

configTransactionObjectsWithViolations=query.TQueryConfig(
	countH	= "#NbOfTransactionViolations",
	countQ	= """SELECT COUNT(0) FROM (
-- -- -- begin -- -- --
--
"""+queryTransactionObjectsWithViolations_byX_base+"""--
-- -- -- end -- -- --
) AS InnerQuery
""",
	selectH	= "#0/A:LocalObjectId|1/B:ObjectName|2/C:CentralObjectId|"\
	"3/D:MetricId|4/E:MetricName|"\
    "5/F:BCriterionId|6/G:BCriterionName|7/H:TCriterionId|8/I:TCriterionName|"\
	"9/J:TWeight|10/K:MWeight|11/L:TCrit|12/M:MCrit|"\
	"13/N:TransactionId|14/O:TransactionName|"\
	"15/P:ObjectFullname|16/Q:TransactionFullname",
	selectQ	= queryTransactionObjectsWithViolations_byX_base
)

