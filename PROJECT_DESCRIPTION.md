# Description Technique Complete du Projet : Assistant de Cours RAG Francophone

Ce document fournit les specifications techniques exhaustives, les choix d'architecture, la modelisation des donnees et les procedures operationnelles du projet **WORKSHOP-EIC**.

---

## 1. Objectif et Perimetre du Projet

L'objectif de ce projet est de concevoir, deployer et maintenir un assistant pedagogique interactif de type RAG (*Retrieval-Augmented Generation*), integralement francophone, execute sur architecture CPU standard sans aucun recours a des API tierces payantes ni a des composants d'infrastructure lourds.

Le systeme repond a des questions formulees en francais par des etudiants sur des supports de cours au format PDF. Ses reponses sont strictement limitees aux documents fournis, assorties de citations formelles identifiant le fichier source et la page exacte, et le systeme applique une politique de refus explicite en l'absence d'information pertinente.

---

## 2. Exigences Fonctionnelles

1. **Extraction de documents** : Parcourir le repertoire `data/`, detecter l'ensemble des fichiers PDF et en extraire le texte intelligible, page apres page, sans perte d'information textuelle.
2. **Segmentation en unites de sens (Chunking)** : Segmenter le texte de chaque page en fragments de taille homogene avec une zone de recouvrement pour preserver le contexte linguistique inter-fragments.
3. **Indexation vectorielle deterministe** : Transformer les fragments en vecteurs semantiques a l'aide d'un modele d'embedding CPU leger et enregistrer ces vecteurs de maniere persistante dans une collection ChromaDB locale.
4. **Recherche semantique par similarite cosinus** : Analyser les questions saisies par l'utilisateur, calculer leur vecteur et retrouver les fragments les plus proches.
5. **Filtrage par seuil de confiance** : Evaluer la distance cosinus des resultats. Si le score depasse le seuil toléré, le systeme refuse immediatement de repondre.
6. **Synthese controlee par LLM** : Soumettre un prompt directif a un modele seq2seq local afin de generer une synthese concise a partir des extraits recuperes.
7. **Attribution deterministe des sources** : Construire les citations a partir des metadonnees du moteur d'extraction, sans confier la mise en forme des sources au LLM.
8. **Interface web interactive** : Proposer un formulaire ergonomique, accessible et reactif communiquant par API REST avec le serveur Flask.

---

## 3. Exigences Non Fonctionnelles

- **Souverainete et vie privee** : Aucune donnee ne transite sur un reseau externe ; le traitement est 100% local.
- **Cout d'exploitation nul** : Pas d'abonnement, pas de jetons payants, aucun service payant.
- **Portabilite** : Compatible Linux, macOS et Windows avec Python 3.10+.
- **Performance CPU** : Modelisation optimisee pour tourner sur des processeurs portables grand public sans necessiter de GPU dedie.
- **Zero bibliotheque JavaScript ou CSS externe** : Aucun CDN, aucun framework tiers (ni React, ni Bootstrap, ni Tailwind). Tout le frontend repose sur les standards HTML5, CSS3 et ECMAScript purs.
- **Zero bibliotheque d'orchestration opaque** : Aucune dependance a LangChain ou LlamaIndex, garantissant une lisibilite totale et un controle rigoureux de la logique metier.
- **Accessibilite et ergonomie** : Cibles tactiles d'au moins 44x44 pixels, indicateurs de focus visibles, palette a contraste eleve et prise en charge de `prefers-reduced-motion`.

---

## 4. Arborescence Complete du Projet

```
WORKSHOP-EIC/
├── .env.example
├── .gitignore
├── README.md
├── PROJECT_DESCRIPTION.md
├── requirements.txt
├── .github/
│   └── pull_request_template.md
├── data/
│   ├── cours_html_css.pdf
│   ├── cours_python.pdf
│   └── cours_sql.pdf
├── scripts/
│   └── generate_sample_pdfs.py
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── ingest.py
│   ├── embed.py
│   ├── rag.py
│   └── app.py
├── interface/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/
│   ├── test_ingest.py
│   ├── test_rag.py
│   └── test_api.py
├── artifacts/
│   └── chunks.jsonl
└── db/
    └── [donnees persistantes ChromaDB]
```

---

## 5. Role Detaille de Chaque Fichier

- `.env.example` : Modele de configuration listant l'ensemble des variables d'environnement ajustables avec leurs valeurs par defaut recommandees.
- `.gitignore` : Regles d'exclusion pour les caches Python, la base vectorielle locale, les artefacts generes, l'environnement virtuel et les fichiers specifiques aux IDE.
- `requirements.txt` : Liste explicite des dependances Python avec versions minimales recommandees.
- `README.md` : Guide d'accueil et documentation pedagogique destinee a un etudiant debutant en IA et en developpement.
- `PROJECT_DESCRIPTION.md` : Specifications techniques globales, architecture, modeles de donnees et manuel de maintenance.
- `.github/pull_request_template.md` : Canevas standardise pour toute proposition de fusion de code au sein du depot.
- `scripts/generate_sample_pdfs.py` : Script autonome produisant trois PDF de cours techniques multi-pages contenant des donnees verifiables.
- `src/__init__.py` : Fichier de marquage faisant du repertoire `src` un package Python importable.
- `src/config.py` : Gestion centralisee et validation stricte de la configuration chargee depuis les variables d'environnement.
- `src/ingest.py` : Moteur d'extraction page par page, nettoyage des textes et fragmentation avec sauvegarde dans `artifacts/chunks.jsonl`.
- `src/embed.py` : Service de vectorisation via `sentence-transformers` et gestion de la collection persistante dans `ChromaDB`.
- `src/rag.py` : Pipeline d'interrogation, de deduplication, de filtrage par seuil, de generation de prompt et d'execution du LLM local avec CLI interactif.
- `src/app.py` : Serveur Flask exposant l'interface web et les routes API REST (`/api/health`, `/api/documents`, `/api/ask`).
- `interface/index.html` : Structure semantique de l'application cliente responsive.
- `interface/style.css` : Feuille de style utilisant exclusivement les variables du nuancier bleu et neutre specifie.
- `interface/app.js` : Logique client sans framework pour les requetes asynchrones, la gestion des etats et l'insertion securisee dans le DOM via `textContent`.
- `tests/test_ingest.py` : Tests unitaires du nettoyage de texte, de l'extraction de pages, de la stabilite des identifiants et du chevauchement de chunks.
- `tests/test_rag.py` : Tests du pipeline RAG avec services simules (fakes), verification des citations et du refus systematique hors contexte.
- `tests/test_api.py` : Tests d'integration des routes Flask, des codes d'etat HTTP et de la validation des charges utiles JSON.

---

## 6. Flux de Donnees de Bout en Bout

```
1. Documents PDF sources (data/*.pdf)
   │
   ▼ [pypdf: extract_text page par page]
2. Pages brutes nettoyees
   │
   ▼ [sliding window: taille 900, recouvrement 150]
3. Fragments structures avec metadonnees
   │
   ▼ [ecriture atomique]
4. Fichier d'echange artifacts/chunks.jsonl
   │
   ▼ [sentence-transformers: encode()]
5. Vecteurs de 384 dimensions
   │
   ▼ [ChromaDB: upsert() avec hnsw:space = cosine]
6. Base vectorielle persistante (db/)
   │
   ▲ [Recherche par similarite lors d'une question]
7. Question utilisateur (/api/ask)
   │
   ▼ [Filtre de seuil: distance <= DISTANCE_THRESHOLD]
   ├─► Si distance > seuil : Refus immediat sans appel LLM
   │
   ▼ [Si distance <= seuil : Deduplication des sources]
8. Assemblage du prompt francophone strict
   │
   ▼ [google/flan-t5-small: generate()]
9. Reponse synthetique brute
   │
   ▼ [Formatage deterministe des citations en Python]
10. Reponse finale certifiee renvoyee a l'interface web
```

---

## 7. Processus d'Extraction PDF

L'extraction repose sur `pypdf.PdfReader` :
- Chaque document PDF du dossier `data/` est ouvert successivement.
- L'index de page de `pypdf` (base 0) est converti en numero de page humain (base 1 : `page_num = idx + 1`).
- Le texte brut extrait est passe dans la fonction `clean_text()` qui normalise les sauts de ligne, retours chariot et espaces multiples en une espace unique, tout en preservant la ponctuation et les caracteres accentues.
- Si une page ne produit aucun caractere ou uniquement du blanc, un avertissement explicite est emis sur `sys.stderr` sans interrompre l'analyse des pages suivantes.

---

## 8. Algorithme de Decoupage (Chunking)

Le texte issu d'une meme page est segmente a l'aide d'une fenetre glissante deterministe :
- **Taille de fragment (`CHUNK_SIZE`)** : 900 caracteres par defaut.
- **Zone de recouvrement (`CHUNK_OVERLAP`)** : 150 caracteres par defaut.
- **Pas d'avancement (`step`)** : `CHUNK_SIZE - CHUNK_OVERLAP` (soit 750 caracteres).
- **Regle de confinement** : Un fragment n'amalgame jamais le contenu de deux pages differentes. Le compteur de fragment `chunk_index` repart a 0 pour chaque nouvelle page.

---

## 9. Modele de Metadonnees

Chaque fragment genere dans `artifacts/chunks.jsonl` repond au schema JSON strict suivant :

```json
{
  "id": "cours_python_p2_c0",
  "source": "cours_python.pdf",
  "page": 2,
  "chunk_index": 0,
  "text": "La robustesse logicielle repose sur le bloc try, except et optionnellement finally pour nettoyer les ressources..."
}
```

- `id` : Identifiant stable compose du nom de base du fichier, du numero de page et de l'index du chunk.
- `source` : Nom complet du fichier PDF d'origine.
- `page` : Entier naturel non nul representant la page physique du document.
- `chunk_index` : Position ordonnee du fragment dans la page.
- `text` : Chaine de caracteres du fragment nettoye.

---

## 10. Processus d'Embedding

- **Modele utilise** : `sentence-transformers/all-MiniLM-L6-v2`.
- **Nature de la transformation** : Conversion de chaines textuelles de dimension variable en vecteurs denses a virgule flottante de 384 dimensions.
- **Optimisation** : Execution locale directe sans requete externe, avec conversion directe en tableaux NumPy puis en listes Python standard pour transmission a ChromaDB.

---

## 11. Schema et Persistance ChromaDB

- **Emplacement physique** : Repertoire `db/`.
- **Client** : `chromadb.PersistentClient(path=...)`.
- **Nom de la collection** : `course_chunks`.
- **Espace de metrique** : `{"hnsw:space": "cosine"}`.
- **Politique d'idempotence** : Utilisation exclusive de `collection.upsert()`. Les executions repetees de `src/embed.py` n'engendrent aucun doublon.
- **Purge des orphelins** : Le script compare les identifiants deja presents dans ChromaDB avec ceux du fichier `chunks.jsonl` et supprime automatiquement de la base les elements obsoletes.

---

## 12. Recherche par Similarite et Seuil de Confiance

Lorsqu'une requete est soumise :
1. La question est vectorisee avec le meme modele d'embedding.
2. ChromaDB retourne les `TOP_K` (par defaut 3) plus proches voisins ainsi que leur distance cosinus.
3. Avec la metrique cosinus de ChromaDB, la distance varie de 0.0 (textes identiques) a 2.0 (vecteurs diametralement opposes).
4. Le seuil `DISTANCE_THRESHOLD` est applique (par defaut 0.7) :
   - Tout extrait dont la distance depasse 0.7 est rejete.
   - Si l'ensemble des extraits depasse le seuil, l'assistant refuse categoriquement de repondre sans solliciter le modele de langage.

---

## 13. Strategie de Prompt et Prevention des Hallucinations

Le prompt soumis a `google/flan-t5-small` est concu pour verrouiller le comportement generatif :

```
Reponds a la question suivante en te basant uniquement et strictement sur le contexte ci-dessous. N'invente aucun fait, aucun nom de fichier et aucun numero de page. Si la reponse n'est pas dans le contexte, reponds exactement: 'Information introuvable'.

Contexte:
Extrait 1 (Fichier: cours_python.pdf, Page: 1):
...

Question:
Quelle est la complexite de len() en Python ?

Reponse:
```

Mesures complementaires :
- Parametre de generation deterministe (`do_sample=False`, `temperature=1.0`).
- Si le texte produit contient `'information introuvable'` ou est vide, le systeme substitue la reponse officielle d'indisponibilite.

---

## 14. Construction Deterministe des Citations

Les citations ne sont jamais produites par le LLM mais construites par Python :
1. Les extraits retenus sont dedupliques par paire unique `(source, page)`.
2. Pour chaque source unique, une chaine est formatee :
   `[Source : nom_fichier.pdf, page X]`
3. Ces mentions sont agregees et concatenees a la fin de la reponse textuelle validee :
   `Reponse finale...\n\n[Source : cours_python.pdf, page 1]`

---

## 15. Routes Flask et Exemples d'Echange

### 1. `GET /`
- Sert la page HTML `interface/index.html`.
- Code HTTP : 200.

### 2. `GET /style.css` et `GET /app.js`
- Servent les ressources statiques CSS et JavaScript associees.
- Code HTTP : 200.

### 3. `GET /api/health`
- Verification de vitalite du serveur.
- Reponse 200 OK :
  ```json
  {
    "status": "ok"
  }
  ```

### 4. `GET /api/documents`
- Liste les fichiers PDF presents dans le dossier `data/`.
- Reponse 200 OK :
  ```json
  {
    "documents": [
      "cours_html_css.pdf",
      "cours_python.pdf",
      "cours_sql.pdf"
    ]
  }
  ```

### 5. `POST /api/upload`
- Televerse un nouveau document PDF de cours, l'enregistre dans `data/`, declenche automatiquement son ingestion et son indexation dans ChromaDB, puis recharge le service RAG.
- Format : `multipart/form-data` avec le champ `file`.
- Reponse 200 OK :
  ```json
  {
    "status": "ok",
    "message": "Le document 'cours_reseaux.pdf' a ete ajoute et indexe avec succes.",
    "filename": "cours_reseaux.pdf",
    "documents": [
      "cours_html_css.pdf",
      "cours_python.pdf",
      "cours_reseaux.pdf",
      "cours_sql.pdf"
    ]
  }
  ```

### 6. `POST /api/ask`
- Traitement d'une question utilisateur.
- Exemple de requete :
  ```json
  {
    "question": "Quelle est la complexite temporelle de la fonction len() sur une liste ?"
  }
  ```
- Exemple de reponse 200 OK :
  ```json
  {
    "answer": "En Python, la fonction len() sur une liste renvoie le nombre d elements en complexite temporelle O(1).\n\n[Source : cours_python.pdf, page 1]",
    "sources": [
      {
        "source": "cours_python.pdf",
        "page": 1,
        "chunk_index": 0,
        "text": "La fonction len() sur une liste renvoie le nombre d elements en complexite temporelle O(1).",
        "distance": 0.1842
      }
    ],
    "question": "Quelle est la complexite temporelle de la fonction len() sur une liste ?"
  }
  ```
- Exemples d'erreurs (400 Bad Request) :
  ```json
  {
    "error": "La question ne peut pas etre vide."
  }
  ```

---

## 16. Ergonomie et Comportement du Frontend

- **Zero rechargement de page** : Formulaire intercepte via `addEventListener("submit", ...)`.
- **Raccourci clavier** : Prise en charge du raccourci `Ctrl+Entree` sur la zone de saisie pour soumettre la requete.
- **Protection XSS** : Toutes les insertions dynamiques de contenu dans le DOM emploient strictement `textContent`.
- **Gestion des etats d'interface** :
  - Etat initial : Bloc vide incitatif avec explications.
  - Etat de chargement : Boutons desactives, spinner d'attente anime accessible.
  - Etat d'erreur : Bandeau visible avec message en francais.
  - Etat de reponse : Carte de synthese et liste distincte des sources.

---

## 17. Variables de Configuration

| Variable | Type | Valeur par defaut | Description |
| :--- | :--- | :--- | :--- |
| `EMBEDDING_MODEL` | str | `sentence-transformers/all-MiniLM-L6-v2` | Modele Hugging Face de vectorisation |
| `GENERATION_MODEL` | str | `google/flan-t5-small` | Modele Seq2Seq local pour la synthese |
| `CHUNK_SIZE` | int | `900` | Taille cible des fragments en caracteres |
| `CHUNK_OVERLAP` | int | `150` | Recouvrement entre deux fragments consecutifs |
| `TOP_K` | int | `3` | Nombre maximal de fragments extraits de ChromaDB |
| `DISTANCE_THRESHOLD` | float | `0.7` | Seuil maximal de distance cosinus |
| `HOST` | str | `127.0.0.1` | Adresse IP d'ecoute du serveur Flask |
| `PORT` | int | `5000` | Port TCP d'ecoute du serveur Flask |
| `MAX_NEW_TOKENS` | int | `128` | Nombre maximal de jetons generes par le LLM |

---

## 18. Strategie de Gestion des Erreurs

- **Entrees invalides** : Detection preliminaire cote client (champs vides) puis validation stricte cote serveur Flask avec codes 400.
- **Fichiers manquants** : Messages d'erreur explicites en francais suggerant la commande exacte a lancer pour corriger la situation.
- **Erreurs systeme non interceptees** : Gestionnaire d'erreur Flask 500 renvoyant un JSON neutre sans jamais devoiler de trace d'appel (*stack trace*) au client.

---

## 19. Securite et Confidentialite

- Execution locale sans communication reseau sortante.
- Exclusion formelle de Git des donnees utilisateurs, caches et bases de donnees (`.gitignore`).
- Aucune manipulation de secrets ni d'identifiants administrateurs.
- Sanitisation complete du texte HTML rendu dans le navigateur.

---

## 20. Mesures d'Accessibilite (A11y)

- Balisage HTML5 semantique (`header`, `main`, `section`, `form`, `footer`).
- Attributs ARIA adaptes (`aria-live="polite"` pour les statuts asynchrones, `role="alert"` pour les erreurs).
- Cibles interactives d'au moins 44x44 pixels pour le confort sur ecran tactile.
- Contraste renforce respectant les normes WCAG AA.
- Prise en charge des usagers sensibles au mouvement via `@media (prefers-reduced-motion: reduce)`.

---

## 21. Strategie de Test

La suite de tests automatises verifie l'ensemble des composants critiques sans dependre du telechargement complet des modeles d'IA :
- **Fakes & Mocks** : Injection de dependances pour le modele d'embedding et de generation (`FakeEmbeddingService`, `FakeLLMService`).
- **Tests d'ingestion** : Verification du respect de la pagination debutant a 1, stabilite des identifiants et logique de recouvrement.
- **Tests RAG** : Verification du refus systematique pour question vide ou hors sujet, formatage strict des citations.
- **Tests API** : Validation des routes, de la conformite des schemas JSON et des rejets de requetes malformees.

---

## 22. Limitations Connues et Evolutions Futures

1. **PDF numerises (scannes)** : Le moteur `pypdf` extrait le texte vectoriel natif. Si un cours est une photo scannee, aucun texte n'est extrait. Une extension future consistera a integrer un pipeline OCR base sur Tesseract ou EasyOCR.
2. **Fichiers audio de cours** : Les enregistrements vocaux ou cours magistraux audio ne sont pas directement acceptes. Une evolution possible est l'ajout d'une etape de transcription locale via Whisper.
3. **Documents avec tableaux complexes** : Les tableaux multi-colonnes peuvent voir leur ordre de lecture linearise.

---

## 23. Tableau de Depannage Technique

| Probleme | Cause | Solution |
| :--- | :--- | :--- |
| `FileNotFoundError: Le fichier 'artifacts/chunks.jsonl' est introuvable` | L'ingestion n'a pas ete lancee | Lancer `python src/ingest.py` |
| `Port 5000 is already in use` | Conflit sur le port HTTP | Renseigner `PORT=5001` dans `.env` |
| `ZeroDivisionError / ValueError sur CHUNK_OVERLAP` | Valeur d'overlap invalide dans `.env` | Fixer `CHUNK_OVERLAP` inferieur a `CHUNK_SIZE` |
| `Distance threshold toujours depasse` | Question trop eloignee du vocabulaire du cours | Formuler la question avec les termes cles du support |

---

## 24. Checklist Finale d'Acceptation

- [x] Structure de repertoire creee et conforme.
- [x] Aucun commentaire present dans les codes source et de configuration.
- [x] Trois cours PDF d'exemple generes et valides (au moins deux pages chacun).
- [x] Ingestion executant le decoupage et generant `artifacts/chunks.jsonl`.
- [x] Base vectorielle ChromaDB persistee dans `db/`.
- [x] Tests pytest validant 100% des cas sans telechargement lourd.
- [x] Serveur Flask et interface client operationalises.
- [x] Citations exactes formees par Python et refus effectif hors contexte.

---

## 25. Commandes de Reproduction a Partir d'une Machine Vierge

```bash
cd /home/ysn/Documents
mkdir -p WORKSHOP-EIC
cd WORKSHOP-EIC

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python scripts/generate_sample_pdfs.py
python src/ingest.py
python src/embed.py

pytest -v

python src/app.py
```
