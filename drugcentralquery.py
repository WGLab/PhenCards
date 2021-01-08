import pandas
from pandas.io.sql import read_sql_query
import psycopg2, psycopg2.extras
import sys, logging
from io import StringIO

def Connect(dbhost="unmtid-dbs.net", dbport="5433", dbname="drugcentral", dbusr="drugman", dbpw="dosage"):
    """Connect to db; specify default cursor type DictCursor."""
    dsn = ("host='%s' port='%s' dbname='%s' user='%s' password='%s'"%(dbhost, dbport, dbname, dbusr, dbpw))
    dbcon = psycopg2.connect(dsn)
    dbcon.cursor_factory = psycopg2.extras.DictCursor
    return dbcon

def Version(dbcon, dbschema="public", fout=None):
    sql = (f"SELECT * FROM {dbschema}.dbversion")
    logging.debug("SQL: {}".format(sql))
    df = read_sql_query(sql, dbcon)
    if fout: return df.to_csv(fout, "\t", index=False)
    return df

def ListTables(dbcon, dbschema="public", fout=None):
  '''Listing the tables.'''
  sql = (f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{dbschema}'")
  df = read_sql_query(sql, dbcon)
  logging.info(f"n_out: {df.shape[0]}")
  if fout: return df.to_csv(fout, "\t", index=False)
  return df

def ListColumns(dbcon, dbschema="public", fout=None):
    df=None;
    sql1 = (f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{dbschema}'")
    df1 = read_sql_query(sql1, dbcon)
    for tname in df1.table_name:
        df=None
        sql2 = (f"SELECT column_name,data_type FROM information_schema.columns WHERE table_schema = '{dbschema}' AND table_name = '{tname}'")
        df_this = read_sql_query(sql2, dbcon)
        df_this["schema"] = dbschema
        df_this["table"] = tname
        df = df_this if df is None else pandas.concat([df, df_this])
        df = df[["schema", "table", "column_name", "data_type"]]
        if fout: df.to_csv(fout, "\t", index=False)
        logging.info(f"n_out: {df.shape[0]}")
    return df

def getDrugData(dbcon, HPOquery, column="concept_name", tname="omop_relationship", dbschema="public", fout=None):
    HPOquery=HPOquery.replace("_"," ").replace("+"," ")
    sql2 = (f"SELECT * FROM {tname} WHERE {column} ILIKE '%{HPOquery}%'")
    df = read_sql_query(sql2, dbcon)
    if fout: df.to_csv(fout, "\t", index=False)
    logging.info(f"n_out: {df.shape[0]}")
    return df

def getDrugInfo(dbcon, id, column="concept_name", tname="omop_relationship", dbschema="public", fout=None):
    sql2 = (f"SELECT * FROM {tname} WHERE {column} = {id}")
    df = read_sql_query(sql2, dbcon)
    if fout: df.to_csv(fout, "\t", index=False)
    logging.info(f"n_out: {df.shape[0]}")
    return df

if __name__ == '__main__':
    dbcon = Connect()
    output = StringIO()
    Version(dbcon, fout=output)
    # ListTables(dbcon, fout=output)
    # ListColumns(dbcon, fout=output)
    # FAERS
    getDrugData(dbcon, "cancer", column="meddra_name", tname="faers", fout=output)
    # OMOP
    getDrugData(dbcon, "cancer", column="concept_name", tname="omop_relationship", fout=output)
    # INFO on drug, get ID from above...
    getDrugInfo(dbcon, "489", column="id", tname="synonyms", fout=output)
    # DDIs on drug, get name from above...
    getDrugData(dbcon, "carbamazepine", column="drug_class1", tname="ddi", fout=output)
    print(output.getvalue())
