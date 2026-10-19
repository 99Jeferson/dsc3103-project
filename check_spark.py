import os
import sys
from importlib import import_module

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

try:
	SparkSession = import_module("pyspark.sql").SparkSession
except ModuleNotFoundError as exc:
	if exc.name == "pyspark":
		raise SystemExit("PySpark is not installed. Install it with: python -m pip install pyspark") from exc
	raise

spark = SparkSession.builder.master("local[*]").appName("check").getOrCreate()
print("Spark version:", spark.version)
print("Rows:", spark.range(1_000_000).count())
spark.stop()
