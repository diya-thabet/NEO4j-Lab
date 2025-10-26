# -*- coding: utf-8 -*-
"""
Script Python pour exécuter l'intégralité du TP Neo4j.
Ce script se connecte à un serveur Neo4j local (Docker),
nettoie la base, importe les données, crée les indexes,
et exécute toutes les requêtes d'analyse.

Prérequis :
1. pip install neo4j
2. Le conteneur Docker Neo4j doit être en cours d'exécution.
3. Les fichiers CSV doivent être dans le volume d'import du conteneur
   et avoir été nettoyés manuellement (ex: lignes "Magdeburg", "Szczecin").
"""
import sys
from neo4j import GraphDatabase

# --- Configuration de la Connexion ---
# (Basé sur notre configuration Docker)
URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "00000000")

# =============================================================================
# DÉFINITION DE TOUTES LES REQUÊTES DU TP
# =============================================================================

# --- ÉTAPE 1 : Requêtes de Setup (Modification de la base) ---
setup_queries = [
    (
        "Nettoyage complet de la base de données",
        "MATCH (n) DETACH DELETE n"
    ),
    (
        "III-1. Importation de 'airport.csv'",
        """
        LOAD CSV WITH HEADERS FROM "file:/airports.csv" as l
        CREATE (airport:Airport{id:toInteger(l.AirportID), name:l.Name, city:l.City,
        country:l.Country, IATA:l.IATA, latitude:toFloat(l.Latitude),
        longitude: toFloat(l.Longitude), altitude: toFloat(l.Altitude), TimeZone:l.TZ})
        """
    ),
    (
        "III-2. Importation de 'airlines.csv'",
        """
        LOAD CSV WITH HEADERS FROM "file:/airlines.csv" as l
        CREATE (airline:Airline{id:toInteger(l.AirlineID), name:l.Name, alias:l.Alias, IATA:l.IATA,
        country:l.Country, active:l.Active})
        """
    ),
    (
        "III-3. Création Index (1/7) - Airport ID",
        "CREATE INDEX airport_id_index FOR (n:Airport) ON (n.id)"
    ),
    (
        "III-3. Création Index (2/7) - Airline ID",
        "CREATE INDEX airline_id_index FOR (n:Airline) ON (n.id)"
    ),
    (
        "III-3. Création Index (3/7) - Route ID",
        "CREATE INDEX route_id_index FOR (n:Route) ON (n.id)"
    ),
    (
        "III-3. Création Index (4/7) - Airport Country",
        "CREATE INDEX airport_country_index FOR (n:Airport) ON (n.country)"
    ),
    (
        "III-3. Création Index (5/7) - Airport City",
        "CREATE INDEX airport_city_index FOR (n:Airport) ON (n.city)"
    ),
    (
        "III-3. Création Index (6/7) - Airport IATA",
        "CREATE INDEX airport_iata_index FOR (n:Airport) ON (n.IATA)"
    ),
    (
        "III-3. Création Index (7/7) - Route Name",
        "CREATE INDEX route_name_index FOR (n:Route) ON (n.name)"
    ),
    (
        "III-4. Création des nœuds d'itinéraires (Syntaxe moderne)",
        """
        LOAD CSV WITH HEADERS FROM "file:/routes.csv" as l
        CALL {
            WITH l
            MERGE (airline:Airline {id: toInteger(l.AirlineID)})
            MERGE (source:Airport {id: toInteger(l.SourceAirportID)})
            MERGE (dest:Airport {id: toInteger(l.DestAirportID)})
            CREATE (route:Route {equipment: l.Equipment})
            CREATE (route)-[:from]->(source)
            CREATE (route)-[:to]->(dest)
            CREATE (route)-[:by]->(airline)
        } IN TRANSACTIONS OF 1000 ROWS
        """
    ),
    (
        "V-1. Création des relations homogènes :path",
        """
        MATCH (FROM:Airport) <-[:from]- (r:Route) -[:to]-> (TO:Airport), (r) -[:by]-> (comp)
        WHERE FROM <> TO
        MERGE (FROM)-[:path {airline: comp.name}]->(TO)
        """
    ),
    (
        "V-2. Création de l'index sur la relation :path",
        "CREATE INDEX path_airline_idx FOR ()-[r:path]-() ON (r.airline)"
    )
]

# --- ÉTAPE 2 : Requêtes d'Analyse (Lecture de la base) ---
analysis_queries = [
    (
        "IV-1. Nom et IATA des aéroports de France",
        """
        MATCH (a:Airport {country: 'France'})
        RETURN a.name AS Nom, a.IATA AS CodeIATA
        LIMIT 20
        """
    ),
    (
        "IV-2. Compagnies aériennes françaises actives avec IATA",
        """
        MATCH (a:Airline {country: 'France', active: 'Y'})
        WHERE a.IATA IS NOT NULL AND a.IATA <> '\\N'
        RETURN a.name AS Nom, a.IATA AS CodeIATA
        """
    ),
    (
        "IV-3. Compagnies françaises avec au moins une route",
        """
        MATCH (a:Airline {country: 'France'})<-[:by]-(:Route)
        RETURN DISTINCT a.name AS Nom
        """
    ),
    (
        "IV-4. Graphe des routes au départ de CDG (Affichage textuel)",
        """
        MATCH (cdg:Airport {IATA: 'CDG'})<-[:from]-(r:Route)-[:to]->(dest:Airport)
        MATCH (r)-[:by]->(airline:Airline)
        RETURN cdg.name AS Depart, airline.name AS Compagnie, dest.name AS Arrivee
        LIMIT 20
        """
    ),
    (
        "IV-5. Graphe des routes au départ de CDG par A380 (Affichage textuel)",
        """
        MATCH (cdg:Airport {IATA: 'CDG'})<-[:from]-(r:Route)-[:to]->(dest:Airport)
        WHERE r.equipment CONTAINS 'A380'
        MATCH (r)-[:by]->(airline:Airline)
        RETURN airline.name AS Compagnie, dest.name AS Arrivee, r.equipment AS Materiel
        """
    ),
    (
        "IV-6. Villes et Pays de destination (départ CDG, A380)",
        """
        MATCH (cdg:Airport {IATA: 'CDG'})<-[:from]-(r:Route)-[:to]->(dest:Airport)
        WHERE r.equipment CONTAINS 'A380'
        RETURN DISTINCT dest.city AS Ville, dest.country AS Pays
        """
    ),
    (
        "IV-7. Villes, Pays et Compagnie (départ CDG, A380)",
        """
        MATCH (cdg:Airport {IATA: 'CDG'})<-[:from]-(r:Route)-[:to]->(dest:Airport)
        WHERE r.equipment CONTAINS 'A380'
        MATCH (r)-[:by]->(airline:Airline)
        RETURN DISTINCT dest.city AS Ville, dest.country AS Pays, airline.name AS Compagnie
        """
    ),
    (
        "IV-8. Itinéraires entre CDG et aéroports français (Affichage textuel)",
        """
        MATCH (cdg:Airport {IATA: 'CDG'})<-[:from]-(:Route)-[:to]->(dest:Airport {country: 'France'})
        RETURN "CDG -> France" AS Direction, dest.name AS AeroportFrancais
        LIMIT 10
        UNION
        MATCH (src:Airport {country: 'France'})<-[:from]-(:Route)-[:to]->(cdg:Airport {IATA: 'CDG'})
        RETURN "France -> CDG" AS Direction, src.name AS AeroportFrancais
        LIMIT 10
        """
    ),
    (
        "IV-9. Toutes les routes par A380 (Affichage textuel)",
        """
        MATCH (src:Airport)<-[:from]-(r:Route)-[:to]->(dest:Airport)
        WHERE r.equipment CONTAINS 'A380'
        MATCH (r)-[:by]->(airline:Airline)
        RETURN src.IATA AS Depart, dest.IATA AS Arrivee, airline.name AS Compagnie
        LIMIT 20
        """
    ),
    (
        "IV-10. Routes : France vers Royaume-Uni (UK) (Affichage textuel)",
        """
        MATCH (src:Airport {country: 'France'})<-[:from]-(r:Route)-[:to]->(dest:Airport {country: 'United Kingdom'})
        MATCH (r)-[:by]->(airline:Airline)
        RETURN src.IATA AS Depart, dest.IATA AS Arrivee, airline.name AS Compagnie
        LIMIT 20
        """
    ),
    (
        "V-3. Graphe des paths 'Air France' entre aéroports français (Affichage textuel)",
        """
        MATCH p = (a:Airport {country: 'France'})-[r:path {airline: 'Air France'}]->(b:Airport {country: 'France'})
        RETURN a.IATA AS Depart, b.IATA AS Arrivee
        LIMIT 20
        """
    ),
    (
        "V-4. Nombre de paths 'Air France' par pays destination",
        """
        MATCH (a:Airport)-[r:path {airline: 'Air France'}]->(b:Airport)
        RETURN b.country AS PaysDestination, count(r) AS NombreDePaths
        ORDER BY NombreDePaths DESC
        """
    ),
    (
        "V-5. Chemins (longueur 2-3) de Nantes à Salt Lake City (Affichage textuel)",
        """
        MATCH p = (nantes:Airport {city: 'Nantes'})-[:path*2..3]->(slc:Airport {city: 'Salt Lake City'})
        RETURN [n IN nodes(p) | n.IATA] AS Chemin, length(p) AS Sauts
        LIMIT 10
        """
    ),
    (
        "V-6. Chemin le plus court de Nantes à Salt Lake City (Affichage textuel)",
        """
        MATCH p = shortestPath(
          (nantes:Airport {city: 'Nantes'})-[:path*1..10]->(slc:Airport {city: 'Salt Lake City'})
        )
        RETURN [n IN nodes(p) | n.IATA] AS CheminLePlusCourt, length(p) AS Sauts
        """
    )
]

# =============================================================================
# FONCTIONS D'EXÉCUTION
# =============================================================================

def run_write_query(session, query, description):
    """Exécute une requête qui modifie la base de données (écritures)."""
    print(f"\n--- Exécution : {description} ---")
    try:
        # .consume() force l'exécution et attend la fin
        summary = session.run(query).consume()
        print(f"Succès. {summary.counters}")
    except Exception as e:
        print(f"ERREUR lors de l'exécution de '{description}': {e}", file=sys.stderr)
        # On arrête le script si une étape de setup échoue
        raise e

def run_read_query(session, query, description):
    """Exécute une requête qui lit les données et affiche les résultats."""
    print(f"\n--- Analyse : {description} ---")
    try:
        result = session.run(query)
        keys = result.keys()
        
        if not keys:
            print("Requête exécutée, pas de résultat tabulaire à afficher.")
            return

        # Affichage des en-têtes
        print(" | ".join([str(k) for k in keys]))
        print("-" * (sum(len(k) for k in keys) + 3 * len(keys)))
        
        count = 0
        for record in result:
            # Formatage de chaque ligne
            values = [str(record[k]) for k in keys]
            print(" | ".join(values))
            count += 1
        
        if count == 0:
            print("(Aucun résultat trouvé)")
        else:
            print(f"({count} lignes retournées)")

    except Exception as e:
        print(f"ERREUR lors de l'analyse '{description}': {e}", file=sys.stderr)

# =============================================================================
# SCRIPT PRINCIPAL
# =============================================================================

def main():
    """Fonction principale pour se connecter et exécuter toutes les requêtes."""
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("="*50)
            print("Connexion à Neo4j ( {URI} ) réussie !".format(URI=URI))
            print("="*50)

            # Utiliser une session pour toutes les opérations
            # Le driver Python gère les transactions automatiquement
            # donc pas besoin de s'inquiéter du ":auto"
            with driver.session() as session:
                
                print("\n=== ÉTAPE 1: SETUP ET IMPORTATION DES DONNÉES ===")
                for description, query in setup_queries:
                    run_write_query(session, query, description)
                    
                print("\n\n=== ÉTAPE 2: EXÉCUTION DES REQUÊTES D'ANALYSE ===")
                for description, query in analysis_queries:
                    run_read_query(session, query, description)
                    
            print("\n\n=== Script terminé avec succès ===")

    except Exception as e:
        print(f"ERREUR: Impossible de se connecter à la base de données à {URI}", file=sys.stderr)
        print(f"Détails : {e}", file=sys.stderr)
        print("\nVeuillez vous assurer que votre conteneur Docker Neo4j est en cours d'exécution.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
