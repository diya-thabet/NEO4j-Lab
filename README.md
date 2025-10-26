# TP Analyse de Données Aériennes avec Neo4j

Ce projet est une implémentation complète d'un travail pratique (TP) universitaire utilisant la base de données orientée graphe **Neo4j** pour analyser un jeu de données sur les aéroports, les compagnies aériennes et les routes (itinéraires) mondiales.

Le projet consiste en un **script Python unique (`script_tp_neo4j.py`)** qui automatise l'ensemble du processus :

1. Connexion à un serveur Neo4j (via Docker).

2. Nettoyage complet de la base de données.

3. Importation et modélisation des données à partir de fichiers CSV (`airports.csv`, `airlines.csv`, `routes.csv`).

4. Création des index et des relations optimisées (`:path`).

5. Exécution d'une série complète de requêtes Cypher (simples et complexes) pour analyser le graphe.

## 🚀 Objectif

L'objectif est de démontrer la puissance de Neo4j et du langage Cypher pour modéliser des réseaux connectés (comme les routes aériennes) et effectuer des requêtes complexes telles que la recherche de chemins, l'analyse de connectivité et le filtrage avancé.

## 🛠️ Prérequis

Avant de lancer le script, vous aurez besoin de :

* **Python 3.x**

* La bibliothèque Python `neo4j`: `pip install neo4j`

* **Docker Desktop** ou Docker Engine (pour lancer la base de données Neo4j)

* Les **fichiers CSV** du jeu de données (non inclus dans ce repo).

## 🏃‍♂️ Comment l'exécuter

### 1. Préparer les données CSV

Ce script s'attend à ce que les fichiers `airports.csv`, `airlines.csv`, et `routes.csv` soient présents.

* **Important :** Le fichier `airports.csv` de ce TP contenait des lignes mal formatées (guillemets et caractères d'échappement incorrects). Ces lignes doivent être **nettoyées manuellement** avant l'importation.

### 2. Lancer la base de données Neo4j (Docker)

Placez vos fichiers CSV nettoyés dans un dossier (ex: `/chemin/vers/vos/csv`). Lancez ensuite le conteneur Docker en montant ce dossier comme volume :
