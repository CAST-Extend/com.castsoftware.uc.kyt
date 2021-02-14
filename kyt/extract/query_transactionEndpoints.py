from extract import query



##== List of transaction endpoints ------------------------------------------
##== Transaction objects that are endpoints of a transaction
# {0}: local schema name, {1}: transaction name
queryListOfTransactionEndpoints_byX_base_DEPRECATED="""\
SELECT
	OT.object_id AS "TransactionId", OT.object_name AS "TransactionName",
	O.object_id AS "EndpointId", O.object_name AS "EndpointName",
	O.object_type_Str "EndpointType", O.object_fullname AS "EndpointFullname",
	OT.object_type_str "TransactionType",
	OT.object_fullname AS "TransactionFullname"
FROM
	{0}.dss_transaction			T
	JOIN {0}.cdt_objects		OT	ON OT.object_id = T.form_id
	JOIN {0}.dss_objects		OT2	ON OT2.object_id = T.object_id
	JOIN {0}.dss_links			L	ON L.previous_object_id = OT2.object_id
	JOIN {0}.cdt_objects		O	ON O.object_id = L.next_object_id
	JOIN {0}.fp_dataendpoints	E	ON E.object_id=O.object_id
WHERE 1=1
    AND OT.object_{2} = {1}
"""

queryListOfTransactionEndpoints_byX_base="""\
SELECT
	OT.object_id AS "TransactionId", OT.object_name AS "TransactionName",
	O.object_id AS "EndpointId", O.object_name AS "EndpointName",
	O.object_type_Str "EndpointType", O.object_fullname AS "EndpointFullname",
	OT.object_type_str "TransactionType",
	OT.object_fullname AS "TransactionFullname"
FROM
	{0}.dss_transaction			T
	JOIN {0}.cdt_objects		OT	ON OT.object_id = T.form_id
	JOIN {0}.dss_objects		OT2	ON OT2.object_id = T.object_id
	--
	JOIN {0}.dss_transactiondetails		DT	ON DT.object_id = OT2.object_id
    JOIN {0}.cdt_objects		O	ON O.object_id = DT.child_id
	JOIN {0}.fp_dataendpoints	E	ON E.object_id=O.object_id
WHERE 1=1
    AND OT.object_{2} = {1}
"""


configTransactionEndpoints=query.TQueryConfig(
	countH	= "#NbOfTransactionEndpoints",
	countQ	= """SELECT COUNT(0) FROM (
-- -- -- begin -- -- --
--
"""+queryListOfTransactionEndpoints_byX_base+"""--
-- -- -- end -- -- --
) AS InnerQuery
""",
	selectH	= "#0/A:TransactionId|1/B:TransactionName|2/C:EndpointId|3/D:EndpointName|4/E:EndpointType[5/F:EndpointFullname|6/F:TransactionType|7/G:transactionFullname",
	selectQ	= queryListOfTransactionEndpoints_byX_base
)