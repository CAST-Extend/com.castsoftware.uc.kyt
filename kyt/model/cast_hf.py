import collections

THealthFactor = collections.namedtuple( "THealthFactor", [ "name", "shortname", "num" ] )

TQI             = THealthFactor( "TQI",             "TQI",  "60017" )
ROBUSTNESS      = THealthFactor( "Robustness",      "ROB",  "60013" )
EFFICIENCY      = THealthFactor( "Efficiency",      "EFF",  "60014" )
SECURITY        = THealthFactor( "Security",        "SEC",  "60016" )
CHANGEABILITY   = THealthFactor( "Changeability",   "CHNG", "60012" )
TRANSFERABILITY = THealthFactor( "Transferability", "TRSF", "60011" )

HEALTH_FACTORS = [ TQI, ROBUSTNESS, EFFICIENCY, SECURITY, CHANGEABILITY, TRANSFERABILITY )