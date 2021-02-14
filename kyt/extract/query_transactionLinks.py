from extract import query



##== Transaction links ------------------------------------------------------
## 2e - Given a transaction name/id, count of transaction links
queryTransactionLinks_byX_base_DEPRECATED="""\
SELECT
    OT.object_id AS TransactionId,
    O1.object_id, O2.object_id,
    OT.object_name AS TransactionName, OT.object_fullname AS TransactionFullname,
    O1.object_name, O1.object_fullname,
    O2.object_name, O2.object_fullname,
    LT.link_type_name, LT.link_type_description
FROM
	-- Retrieve transaction
	{0}.cdt_objects		OT
	JOIN {0}.dss_transaction	T	ON T.form_id = OT.object_id
	JOIN {0}.dss_objects	OT2	ON OT2.object_id = T.object_id
	--
	-- retrieve potential callers (ie object involved in transaction)
	JOIN {0}.dss_links		L1	ON L1.previous_object_id = OT2.object_id
	JOIN {0}.cdt_objects	O1	ON O1.object_id = L1.next_object_id
	--
	-- retrieve calleds (object called by the caller, and involved in transaction)
	JOIN {0}.ctv_links		TL	ON TL.caller_id=O1.object_id
	JOIN {0}.cdt_objects	O2	ON O2.object_id = TL.called_id
	JOIN {0}.dss_links		L2	ON L2.previous_object_id = OT2.object_id
								AND L2.next_object_id=O2.object_id
	LEFT JOIN {0}.ctv_link_types    LT	ON LT.link_type_hi = TL.link_type_hi
										AND LT.link_type_lo = TL.link_type_lo
										AND LT.link_type_hi2 = TL.link_type_hi2
										AND LT.link_type_lo2 = TL.link_type_lo2
WHERE
	OT.object_{2} = {1}
	AND OT2.object_type_id = 30002
"""

queryTransactionLinks_byX_base="""\
SELECT
    OT.object_id AS TransactionId,
    O1.object_id, O2.object_id,
    OT.object_name AS TransactionName, OT.object_fullname AS TransactionFullname,
    O1.object_name, O1.object_fullname,
    O2.object_name, O2.object_fullname,
    LT.link_type_name, LT.link_type_description
FROM
	-- Retrieve transaction
	{0}.cdt_objects		OT
	JOIN {0}.dss_transaction	T	ON T.form_id = OT.object_id
	JOIN {0}.dss_objects	OT2	ON OT2.object_id = T.object_id
	--
	-- retrieve potential callers (ie object involved in transaction)
	----JOIN sicas_local.dss_links		L1	ON L1.previous_object_id = OT2.object_id
	----JOIN sicas_local.cdt_objects	O1	ON O1.object_id = L1.next_object_id
	JOIN {0}.dss_transactiondetails		DT	ON DT.object_id = OT2.object_id
	JOIN {0}.cdt_objects 	O1	ON O1.object_id = DT.child_id
	--
	-- retrieve calleds (object called by the caller, and involved in transaction)
	JOIN {0}.ctv_links		TL	ON TL.caller_id=O1.object_id
	JOIN {0}.cdt_objects	O2	ON O2.object_id = TL.called_id
	----JOIN sicas_local.dss_links		L2	ON L2.previous_object_id = OT2.object_id
	----							AND L2.next_object_id=O2.object_id
	JOIN {0}.dss_transactiondetails		DT2	ON  DT2.object_id = OT2.object_id
												AND DT2.child_id=O2.object_id
	LEFT JOIN {0}.ctv_link_types    LT	ON LT.link_type_hi = TL.link_type_hi
										AND LT.link_type_lo = TL.link_type_lo
										AND LT.link_type_hi2 = TL.link_type_hi2
										AND LT.link_type_lo2 = TL.link_type_lo2
WHERE
	OT.object_{2} = {1}
	AND OT2.object_type_id = 30002
"""

configTransactionLinks=query.TQueryConfig(
	countH	= "#NbOfTransactionLinks",
	countQ	= """SELECT COUNT(0) FROM (
-- -- -- begin -- -- --
--
"""+queryTransactionLinks_byX_base+"""--
-- -- -- end -- -- --
) AS InnerQuery
""",
	selectH	= "#TransactionId|Object1Id|Object2Id|TransactionName|TransactionFullname|Object1Name|Object1Fullname|Object2Name|Object2Fullname|LinkTypeName|LinkTypeDesc",
	selectQ	= queryTransactionLinks_byX_base
)
