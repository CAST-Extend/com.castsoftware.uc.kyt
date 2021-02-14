from extract import query



##== List of transactions ---------------------------------------------------
# {0}: local schema, {1}: criteria value, {2}: criteria:={id|name|fullname}
queryListOfTransactions_byX_base="""\
SELECT
    O.object_language_name	AS "LanguageName",
	O.object_id 			AS "TransactionId",
	O.object_name			AS "TransactionName",
	O.object_type_str		AS "TransactionType",
	O.object_fullname		AS "TransactionFullName"
FROM
    {0}.cdt_objects		        O
    JOIN {0}.dss_transaction	T	ON T.form_id=O.object_id
WHERE 1=1
	AND O.object_{2} = {1}
ORDER BY
	O.object_language_name, O.object_name, O.object_fullname, O.object_id
"""

configTransactions=query.TQueryConfig(
	countH	= "#NbOfTransactions",
	countQ	= """SELECT COUNT(0) FROM (
-- -- -- begin -- -- --
--
"""+queryListOfTransactions_byX_base+"""--
-- -- -- end -- -- --
) AS InnerQuery
""",
	selectH	= "#0/A:LanguageName|1/B:TransactionId|2/C:TransactionName|3/D:TransactionType|4/E:TransactionFullname",
	selectQ	= queryListOfTransactions_byX_base
)