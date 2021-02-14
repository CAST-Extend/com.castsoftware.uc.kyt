from extract import query



##== Objpro for enlihten view -----------------------------------------------
queryTransactionObjpro_byX_base_DEPRECATED="""\
SELECT DISTINCT
	OPRO.idpro from {0}.objpro	OPRO
WHERE
	OPRO.idobj IN (
		-- transaction objects
		SELECT -- DISTINCT
			O.object_id
		FROM
			{0}.dss_transaction	T
			JOIN {0}.cdt_objects	OT	ON OT.object_id = T.form_id
			JOIN {0}.dss_objects	OT2	ON OT2.object_id = T.object_id
			JOIN {0}.dss_links	L	ON L.previous_object_id = OT2.object_id
			JOIN {0}.cdt_objects	O	on O.object_id = L.next_object_id
		WHERE
			OT.object_{2} = {1}	-- <transaction id>
			AND OT2.object_type_id = 30002
	)
"""

queryTransactionObjpro_byX_base="""\
SELECT DISTINCT
	OPRO.idpro from {0}.objpro	OPRO
WHERE
	OPRO.idobj IN (
		-- transaction objects
		SELECT -- DISTINCT
			O.object_id
		FROM
			{0}.dss_transaction	T
			JOIN {0}.cdt_objects	OT	ON OT.object_id = T.form_id
			JOIN {0}.dss_objects	OT2	ON OT2.object_id = T.object_id
			--JOIN {0}.dss_links	L	ON L.previous_object_id = OT2.object_id
	        JOIN {0}.dss_transactiondetails		DT	ON DT.object_id = OT2.object_id
			JOIN {0}.cdt_objects	O	on O.object_id = DT.child_id
		WHERE
			OT.object_{2} = {1}	-- <transaction id>
			AND OT2.object_type_id = 30002
	)
"""
configTransactionObjPro=query.TQueryConfig(
	countH	= "#NbOfObjproId",
	countQ	= """SELECT COUNT(0) FROM (
-- -- -- begin -- -- --
--
"""+queryTransactionObjpro_byX_base+"""--
-- -- -- end -- -- --
) AS InnerQuery
""",
	selectH	= "#ObjproId",
	selectQ	= queryTransactionObjpro_byX_base
)