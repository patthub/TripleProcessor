from sparql_dataframe import get
import pandas as pd
from pandas import read_csv, concat, DataFrame
from rdflib import Graph, URIRef, RDF, Literal
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
import json
import requests


print("Hello, world!")