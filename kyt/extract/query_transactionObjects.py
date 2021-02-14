from extract import query

##== List of transaction objects --------------------------------------------
## 2c - Given a transaction name/id, count of transaction objects
# 0: local schema name, 1: transaction name, 2: { "id" | "name" | "fullname" }, 3: central_schema
queryTransactionObjectsByX_base_DEPRECATED="""\
SELECT DISTINCT
    OT.object_id AS "TransactionId", OT.object_name AS "TransactionName",  OT.object_type_str "TransactionType", OT.object_fullname AS "TransactionFullname",
    A.object_id AS "ArtifactId", A.object_name AS "ArtifactName", A.object_type_Str "ArtifactType", A.object_fullname AS "ArtifactFullname"
FROM
	{0}.cdt_objects		OT
	JOIN {0}.dss_transaction	T	ON T.form_id = OT.object_id
	JOIN {0}.dss_objects	O2	ON O2.object_id = T.object_id
	JOIN {0}.dss_links		L	ON L.previous_object_id = O2.object_id
	JOIN {0}.cdt_objects 	A	ON A.object_id = L.next_object_id
WHERE 1=1
	AND OT.object_{2} = {1}
"""

queryTransactionObjectsByX_base="""\
SELECT DISTINCT
    OT.object_id AS "TransactionId", OT.object_name AS "TransactionName",  OT.object_type_str "TransactionType", OT.object_fullname AS "TransactionFullname",
    A.object_id AS "ArtifactId", A.object_name AS "ArtifactName", A.object_type_Str "ArtifactType", A.object_fullname AS "ArtifactFullname",
    AC.object_id AS "ArtifactCentralId"
FROM
	{0}.cdt_objects		OT
	JOIN {0}.dss_transaction	T	ON T.form_id = OT.object_id
	JOIN {0}.dss_objects	O2	ON O2.object_id = T.object_id
    --
	JOIN {0}.dss_transactiondetails		DT	ON DT.object_id = O2.object_id
	JOIN {0}.cdt_objects 	A	ON A.object_id = DT.child_id
	--
    -- Get central object id
	LEFT JOIN {3}.dss_translation_table	AC
		ON	AC.site_object_id = A.object_id
    --
WHERE 1=1
	AND OT.object_{2} = {1}
"""

configTransactionObjects=query.TQueryConfig(
	countH	= "#NbOfTransactionObjects",
	countQ	= """SELECT COUNT(0) FROM (
-- -- -- begin -- -- --
--
"""+queryTransactionObjectsByX_base+"""--
-- -- -- end -- -- --
) AS InnerQuery
""",
	selectH	= "# 0/A: TransactionId | 1/B: TransactionName | 2/C: TransactionType | 3/D: TransactionFullname | 4/E: ObjectId | 5/F: ObjectName | 6/G: ObjectType | 7/H: ObjectFullname | 8/I: ObjectCentralId",
	selectQ	= queryTransactionObjectsByX_base
)