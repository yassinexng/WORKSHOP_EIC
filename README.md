# Mon Assistant de Cours - RAG Francophone

Assistant de cours intelligent, 100% local, souverain et sans API payante, base sur l'architecture RAG (Retrieval-Augmented Generation). Ce projet permet aux etudiants et enseignants d'interroger interactivement des supports de cours au format PDF et d'obtenir des reponses precises, assorties de citations exactes (nom du fichier et numero de page), tout en eliminant les hallucinations.

---

## Table des matieres

1. [Concepts fondamentaux pour debutants](#1-concepts-fondamentaux-pour-debutants)
   - [Qu'est-ce qu'un LLM ?](#quest-ce-quun-llm-)
   - [Qu'est-ce qu'un embedding (plongement vectoriel) ?](#quest-ce-quun-embedding-plongement-vectoriel-)
   - [Qu'est-ce qu'une base de donnees vectorielle ?](#quest-ce-quune-base-de-donnees-vectorielle-)
   - [Qu'est-ce que le RAG ?](#quest-ce-que-le-rag-)
2. [Architecture globale du projet](#2-architecture-globale-du-projet)
3. [Prerequis systeme](#3-prerequis-systeme)
4. [Installation pas a pas](#4-installation-pas-a-pas)
   - [Creation et activation de l'environnement virtuel](#creation-et-activation-de-lenvironnement-virtuel)
   - [Installation des dependances sans sudo](#installation-des-dependances-sans-sudo)
5. [Guide d'utilisation pas a pas](#5-guide-dutilisation-pas-a-pas)
   - [Etape 1 : Generation des documents PDF de cours](#etape-1--generation-des-documents-pdf-de-cours)
   - [Etape 2 : Ingestion et decoupage des documents](#etape-2--ingestion-et-decoupage-des-documents)
   - [Etape 3 : Calcul des embeddings et indexation ChromaDB](#etape-3--calcul-des-embeddings-et-indexation-chromadb)
   - [Etape 4 : Test interactif dans le terminal (CLI)](#etape-4--test-interactif-dans-le-terminal-cli)
   - [Etape 5 : Lancement de l'application Web](#etape-5--lancement-de-lapplication-web)
6. [Comment remplacer les cours d'exemple par vos propres PDF](#6-comment-remplacer-les-cours-dexemple-par-vos-propres-pdf)
7. [PDF natif contre PDF numerise (scanne)](#7-pdf-natif-contre-pdf-numerise-scanne)
8. [Fonctionnement des citations exactes](#8-fonctionnement-des-citations-exactes)
9. [Prevention des hallucinations et refus de reponse](#9-prevention-des-hallucinations-et-refus-de-reponse)
10. [Execution des tests automatises](#10-execution-des-tests-automatises)
11. [Depannage et erreurs frequentes](#11-depannage-et-erreurs-frequentes)
12. [Gestion de versions avec Git (Workflow collaboratif)](#12-gestion-de-versions-avec-git-workflow-collaboratif)
13. [Regles de securite et confidentialite](#13-regles-de-securite-et-confidentialite)
14. [Checklist finale de validation](#14-checklist-finale-de-validation)

---

## 1. Concepts fondamentaux pour debutants

### Qu'est-ce qu'un LLM ?
Un **LLM** (*Large Language Model*, ou grand modele de langage) est un reseau de neurones artificiels entraine sur des quantites massives de texte. Il est capable de comprendre des questions en langage naturel et de generer du texte coherent mot par mot. Toutefois, un LLM standard ne connait pas vos cours prives et a tendance a inventer des informations plausibles mais fausses lorsqu'il ignore la reponse : c'est le phenomene d'**hallucination**.

### Qu'est-ce qu'un embedding (plongement vectoriel) ?
Un **embedding** est la representation d'un texte (phrase, paragraphe ou mot) sous la forme d'une liste de nombres (un vecteur mathematique). Dans cet espace vectoriel, deux textes qui partagent un sens similaire ou abordent le meme theme se retrouvent proches l'un de l'autre, meme s'ils n'utilisent pas exactement les memes mots. Dans ce projet, nous utilisons le modele ouvert `sentence-transformers/all-MiniLM-L6-v2` qui transforme chaque extrait de texte en un vecteur de 384 dimensions.

### Qu'est-ce qu'une base de donnees vectorielle ?
Une base de donnees relationnelle classique (comme PostgreSQL ou MySQL) recherche des correspondances exactes de mots ou de cles. Une **base de donnees vectorielle** (comme **ChromaDB**) est concue specifiquement pour comparer des vecteurs numeriques en calculant leur similarite geometrique (similarite cosinus). Elle permet de retrouver instantanement, parmi des milliers de fragments de cours, les passages les plus pertinents par rapport a une question posee.

### Qu'est-ce que le RAG ?
Le **RAG** (*Retrieval-Augmented Generation*, ou generation augmentee par recuperation) combine la puissance de recherche d'une base vectorielle et les capacites de synthese d'un LLM. Au lieu de demander directement au modele d'inventer une reponse :
1. On recherche d'abord dans la base vectorielle les extraits de cours les plus pertinents pour la question.
2. On fournit ces extraits au modele de langage en lui donnant la consigne stricte de repondre uniquement avec ce contenu.
3. Si les extraits trouves ne sont pas pertinents, le systeme refuse categoriquement de repondre.
4. L'application annexe automatiquement le nom du fichier PDF et le numero de la page d'ou provient chaque information.

---

## 2. Architecture globale du projet

L'architecture de l'application s'organise en cinq couches distinctes :

```
[ Documents PDF (data/) ]
          │
          ▼
[ Ingestion & Decoupage (src/ingest.py) ] ──► [ Fichier JSONL (artifacts/chunks.jsonl) ]
                                                            │
                                                            ▼
[ Recherche Cosinus (ChromaDB db/) ] ◄── [ Calcul des Embeddings (src/embed.py) ]
          │
          ▼
[ Pipeline RAG (src/rag.py) ] ◄── [ LLM Local : google/flan-t5-small ]
          │
          ▼
[ Backend Web Flask (src/app.py) ] ◄──► [ Interface Utilisateur (interface/) ]
```

---

## 3. Prerequis systeme

- **Systeme d'exploitation** : Linux, macOS ou Windows 10/11.
- **Python** : Version 3.10 ou superieure.
- **Memoire vive (RAM)** : 4 Go minimum (8 Go recommandes pour une execution fluide).
- **Espace disque libre** : 2 Go pour les dependances et les modeles legers.
- **Connexion Internet** : Necessaire une seule fois pour le telechargement initial des bibliotheques et des modeles ouverts Hugging Face. Ensuite, le systeme fonctionne integralement hors-ligne.

---

## 4. Installation pas a pas

### Creation et activation de l'environnement virtuel

Ouvrez un terminal et placez-vous dans le dossier racine du projet `WORKSHOP-EIC` :

#### Sous Linux et macOS :
```bash
cd WORKSHOP-EIC
python3 -m venv .venv
source .venv/bin/activate
```

#### Sous Windows (PowerShell) :
```powershell
cd WORKSHOP-EIC
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### Sous Windows (Invite de commandes cmd.exe) :
```cmd
cd WORKSHOP-EIC
python -m venv .venv
.\.venv\Scripts\activate.bat
```

### Installation des dependances sans sudo

Assurez-vous que votre environnement virtuel est actif (le prefixe `(.venv)` s'affiche a gauche de votre invite de commande), puis installez l'ensemble des bibliotheques requises :

```bash
pip install -r requirements.txt
```

---

## 5. Guide d'utilisation pas a pas

### Etape 1 : Generation des documents PDF de cours

Generez les trois cours d'exemple au format PDF (`cours_html_css.pdf`, `cours_python.pdf`, `cours_sql.pdf`) avec un texte natif et plusieurs pages :

```bash
python scripts/generate_sample_pdfs.py
```

### Etape 2 : Ingestion et decoupage des documents

Extrayez le texte de chaque page, decoupez-le en fragments de recherche (*chunks*) avec chevauchement et enregistrez les metadonnees dans `artifacts/chunks.jsonl` :

```bash
python src/ingest.py
```

### Etape 3 : Calcul des embeddings et indexation ChromaDB

Calculez les vecteurs semantiques a l'aide du modele d'embedding local et inserez-les de maniere persistante dans la collection ChromaDB :

```bash
python src/embed.py
```

### Etape 4 : Test interactif dans le terminal (CLI)

Testez l'assistant directement dans votre console. Posez vos questions et observez la reponse ainsi que les citations exactes. Tapez `quitter` pour quitter le programme :

```bash
python src/rag.py
```

### Etape 5 : Lancement de l'application Web

Demarrez le serveur web local Flask :

```bash
python src/app.py
```

Ouvrez ensuite votre navigateur web a l'adresse exacte suivante :
**http://127.0.0.1:5000**

---

## 6. Comment ajouter ou remplacer des cours par vos propres PDF

Vous disposez de deux methodes simples pour ajouter vos propres cours PDF :

### Methode 1 : Directement depuis l'interface web (Recommande)
1. Ouvrez l'interface sur **http://127.0.0.1:5000**.
2. Dans la section **Ajouter un nouveau support de cours (PDF)**, cliquez sur **Parcourir** et choisissez votre fichier PDF.
3. Cliquez sur **Importer et indexer le cours**.
4. L'application extrait instantanement le texte, calcule les embeddings et met a jour la base vectorielle sans aucun redemarrage requis.

### Methode 2 : En ligne de commande
1. Deposez vos fichiers PDF dans le dossier `data/`.
2. Relancez l'ingestion pour analyser les nouveaux fichiers :
   ```bash
   python src/ingest.py
   ```
3. Relancez l'indexation vectorielle pour mettre a jour la base de donnees :
   ```bash
   python src/embed.py
   ```
4. Interrogez vos nouveaux documents dans l'interface web ou en console.

---

## 7. PDF natif contre PDF numerise (scanne)

Il est fondamental de distinguer deux categories de fichiers PDF :

- **PDF natif** : Document genere numeriquement depuis un traitement de texte (Word, LibreOffice, LaTeX, etc.). Le texte est directement selectionnable a la souris, extractible par programme et exploitable immediatement par notre outil `pypdf`.
- **PDF numerise (scanne)** : Document obtenu par numérisation physique d'une feuille de papier sans reconnaissance optique de caracteres. Le fichier ne contient que des images de pages. `pypdf` ne detecte aucun texte exploitable et emet un avertissement.

Pour exploiter un document scanne, il sera necessaire de passer par une etape preliminaire d'OCR (Reconnaissance Optique de Caracteres, par exemple via Tesseract ou EasyOCR) avant l'ingestion.

---

## 8. Fonctionnement des citations exactes

Pour garantir une confiance totale dans les reponses :
1. Lors du decoupage du PDF, chaque fragment garde en memoire son fichier d'origine et son numero de page reel (commencant a 1).
2. Lorsque les fragments les plus pertinents sont selectionnes, le code Python extrait ces metadonnees.
3. Le systeme Python ajoute a la fin de la reponse la mention sous la forme stricte :
   `[Source : cours_python.pdf, page 2]`
4. Les citations ne sont jamais deleguees a l'imagination du modele de langage.

---

## 9. Prevention des hallucinations et refus de reponse

Pour empecher toute reponse fabriquee :
1. **Filtre de similarite cosinus** : Si la distance entre la question et les fragments de cours depasse le seuil configure (`DISTANCE_THRESHOLD=0.7`), le systeme arrete le traitement avant meme d'interroger le LLM.
2. **Message de refus immuable** : En cas de doute ou d'information absente, le systeme repond strictement :
   `Je ne trouve pas cette information dans les documents fournis.`
3. **Consigne stricte dans le prompt** : Le modele recoit l'instruction formelle d'ignorer ses connaissances pre-entrainees et d'admettre immediatement son incapacite si la reponse ne figure pas mot pour mot dans l'extrait fourni.

---

## 10. Execution des tests automatises

Pour verifier le bon fonctionnement de tous les modules sans telecharger les modeles complets, executez la suite de tests avec pytest :

```bash
pytest
```

Pour afficher le detail de chaque test execute :

```bash
pytest -v
```

---

## 11. Depannage et erreurs frequentes

| Symptome ou Message d'erreur | Cause probable | Solution recommandee |
| :--- | :--- | :--- |
| `FileNotFoundError: Le fichier 'artifacts/chunks.jsonl' est introuvable` | L'etape d'ingestion n'a pas ete executee. | Executez la commande `python src/ingest.py`. |
| `FileNotFoundError: Aucun fichier PDF trouve dans le dossier data/` | Le dossier `data/` est vide. | Executez `python scripts/generate_sample_pdfs.py` ou placez des PDF dans `data/`. |
| `ModuleNotFoundError: No module named 'flask'` | L'environnement virtuel n'est pas active ou les dependances ne sont pas installees. | Activez le venv avec `source .venv/bin/activate` et lancez `pip install -r requirements.txt`. |
| `Address already in use (Port 5000)` | Une autre application utilise deja le port 5000. | Changez le port dans `.env` (`PORT=5001`) ou arretez le processus en conflit. |
| Avertissement page sans texte extractible | Le PDF contient une page blanche ou une image scannee. | Verifiez que le PDF contient bien du texte selectionnable. |

---

## 12. Gestion de versions avec Git (Workflow collaboratif)

Pour developper de nouvelles fonctionnalites dans les regles de l'art sans casser la branche principale :

1. **Creer une branche dediee** :
   ```bash
   git checkout -b feature/nouvelle-fonctionnalite
   ```
2. **Effectuer vos modifications et valider localement** :
   ```bash
   git add src/
   git commit -m "Ajout d une nouvelle fonctionnalite de recherche"
   ```
3. **Pousser la branche vers votre depot distant** :
   ```bash
   git push origin feature/nouvelle-fonctionnalite
   ```
4. **Ouvrir une Pull Request** sur votre forge logicielle (GitHub, GitLab) en complétant le modele fourni dans `.github/pull_request_template.md`.

---

## 13. Regles de securite et confidentialite

- **Confidentialite absolue** : Aucune donnee n'est transmise a des tiers. Tout s'execute sur votre machine locale.
- **Exclusion Git** : Les dossiers `db/`, `artifacts/`, `.venv/` et les fichiers `.env` sont ignores par Git afin d'eviter la fuite accidentelle de donnees locales ou de configurations privees.
- **Aucune clef requise** : Aucun compte ni carte bancaire n'est necessaire.

---

## 14. Checklist finale de validation

- [ ] L'environnement virtuel est cree et active.
- [ ] Les dependances de `requirements.txt` sont installees.
- [ ] Les 3 PDF sont generes dans `data/` et contiennent au moins 2 pages chacun.
- [ ] Le fichier `artifacts/chunks.jsonl` est genere par `src/ingest.py`.
- [ ] La base `db/` est initialisee par `src/embed.py`.
- [ ] La suite de tests `pytest` s'execute avec un score de 100% de reussite.
- [ ] L'interface web repond sur `http://127.0.0.1:5000`.
- [ ] Une question presente dans le cours renvoie une reponse claire avec sa source.
- [ ] Une question absente du cours declenche le refus strict : `Je ne trouve pas cette information dans les documents fournis.`.
