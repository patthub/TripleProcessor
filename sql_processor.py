import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey
import ast
import numpy as np

# Wczytanie danych z pliku CSV
data = pd.read_csv('slownictwo.csv')

# Utworzenie połączenia z bazą danych
engine = create_engine('sqlite:///slownictwo.db')

# Definiowanie metadanych
metadata = MetaData()

# Definiowanie tabel
slownictwo = Table('slownictwo', metadata,
    Column('id', Integer, primary_key=True),
    # ... inne kolumny
)

# Definiowanie tabeli dla relacji
relationship = Table('relationship', metadata,
    Column('Concept', String, primary_key=True),
    Column('slownictwo_id', Integer, ForeignKey('slownictwo.id')),
    Column('relation_type', String),
    Column('value', String),
)

# Tworzenie tabel w bazie danych
metadata.create_all(engine)

# Funkcja pomocnicza do rozbijania wartości z kolumn relacyjnych
def split_relation(row, column_name):
    if pd.isna(row[column_name]):
        return []
    values = ast.literal_eval(str(row[column_name]))  # Konwersja na string, a następnie bezpieczne ocenianie wyrażenia
    return [{'slownictwo_id': row['Concept'], 'relation_type': column_name, 'value': value} for value in values]

# Lista kolumn relacyjnych
relation_columns = [
    'broadMatch', 'exactMatch', 'narrowMatch', 'LOC_ID/exactMatch?close?',
    'altLabel fin_a', 'Fi_Id/exactMatch?close?', 'altLabel cze_a', 'Cze_ID/exactMatch?close?',
    'altLabel field_a_esp', 'esp_ID_exactMatch?close?', 'slownik_Hubar/exactMatch?close?', 'altLabel_pl'
]

# Rozbijanie wartości z kolumn relacyjnych
relationship_data_list = []
for column in relation_columns:
    relationship_data_list.extend(data.apply(split_relation, column_name=column, axis=1).tolist())

relationship_data = pd.DataFrame([item for sublist in relationship_data_list for item in sublist])

# Przekazanie danych do bazy danych
data.to_sql('slownictwo', con=engine, if_exists='replace', index=False)
relationship_data.to_sql('relationship', con=engine, if_exists='replace', index=False)
#####

import pandas as pd
from sqlalchemy import create_engine
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import SKOS

# Mapowanie nazw kolumn na relacje SKOS
column_to_skos_relation = {
    'broadMatch': SKOS.broadMatch,
    'exactMatch': SKOS.exactMatch,
    'narrowMatch': SKOS.narrowMatch,
    'LOC_ID/exactMatch?close?': SKOS.closeMatch,
    'altLabel fin_a': SKOS.altLabel,
    'Fi_Id/exactMatch?close?': SKOS.closeMatch,
    'altLabel cze_a': SKOS.altLabel,
    'Cze_ID/exactMatch?close?': SKOS.closeMatch,
    'altLabel field_a_esp': SKOS.altLabel,
    'esp_ID_exactMatch?close?': SKOS.closeMatch,
    'slownik_Hubar/exactMatch?close?': SKOS.closeMatch,
    'altLabel_pl': SKOS.altLabel,
}

# Ustawienie połączenia z bazą danych
engine = create_engine('sqlite:///slownictwo.db')

# Wczytanie danych z bazy danych SQL
query = f"""
    SELECT * FROM slownictwo
"""
data = pd.read_sql_query(query, engine)

# Utworzenie nowego grafu RDF
g = Graph()

# Utworzenie przestrzeni nazw
n = Namespace("http://example.org/slownictwo/")

# Dodawanie triple'ów do grafu
for index, row in data.iterrows():
    concept = n[row['Concept']]
    for column, skos_relation in column_to_skos_relation.items():
        if pd.notna(row[column]):
            values = row[column].strip("[]").split(", ")
            for value in values:
                related_concept_id = value.strip("'")
                related_concept = n[related_concept_id]
                g.add((concept, skos_relation, related_concept))
    
    # Dodawanie etykiet
    g.add((concept, SKOS.prefLabel, Literal(row['elb_concept/prefLabel?'])))

# Zapisanie grafu do pliku RDF (w formacie XML)
g.serialize(destination='output.rdf', format='xml')
