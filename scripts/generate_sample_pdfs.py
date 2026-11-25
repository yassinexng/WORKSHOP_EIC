import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from pypdf import PdfReader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

COURSE_DOCUMENTS = {
    "cours_html_css.pdf": [
        {
            "title": "Introduction au HTML5 et a la Structure Web",
            "sections": [
                ("1. Principes fondamentaux du HTML5",
                 "Le langage HTML (HyperText Markup Language) structure le contenu des pages web au moyen de balises semantiques. "
                 "Le document debute par la declaration du doctype standard qui informe le navigateur de la version utilisee. "
                 "L element racine html englobe les sections head et body. "
                 "La section head contient les metadonnees indispensables telles que l encodage UTF-8 et le titre de l onglet."),
                ("2. Balises semantiques structurelles",
                 "HTML5 a introduit des balises structurelles majeures pour ameliorer le referencement naturel et l accessibilite. "
                 "La balise header definit l en-tete d une page ou d une section. "
                 "La balise nav regroupe les liens de navigation principaux. "
                 "La balise main contient le contenu central unique de la page. "
                 "La balise article represente une unite de contenu autonome et redistribuable. "
                 "La balise footer marque le pied de page et les mentions legales. "
                 "La balise a necessite l attribut href pour etablir un lien hypertexte vers une autre ressource.")
            ]
        },
        {
            "title": "Feuilles de Style CSS3 et Conception Moderne",
            "sections": [
                ("3. Selecteurs et modele de boite",
                 "CSS (Cascading Style Sheets) gere l apparence graphique et la presentation visuelle des elements HTML. "
                 "Les selecteurs de classe commencent par un point et les identifiants uniques par un croisillon. "
                 "Le modele de boite regroupe quatre couches concentriques successives : le contenu central, la marge interne (padding), "
                 "la bordure exterieure (border) et la marge externe de separation (margin). "
                 "La propriete box-sizing regule la maniere dont les largeurs totales sont calculees."),
                ("4. Flexbox, Grid et Responsive Design",
                 "Flexbox est un module unidimensionnel de disposition concu pour distribuer l espace entre les elements. "
                 "La propriete flex-direction par defaut en CSS Flexbox est row. "
                 "La propriete justify-content gere l alignement horizontal le long de l axe principal. "
                 "CSS Grid propose un systeme bidimensionnel puissant organise en lignes et colonnes. "
                 "Les Media Queries permettent d adapter le style aux dimensions d ecran avec la syntaxe @media (max-width: 768px).")
            ]
        }
    ],
    "cours_python.pdf": [
        {
            "title": "Fondamentaux du Langage de Programmation Python",
            "sections": [
                ("1. Syntaxe et typage dynamique",
                 "Python est un langage de programmation interprete, multi-paradigme et a typage dynamique fort. "
                 "L indentation par espaces remplace les accolades pour delimiter les blocs d instructions. "
                 "Les types primitifs fondamentaux sont les entiers (int), les nombres a virgule flottante (float), "
                 "les chaines de caracteres immutables (str) et les booleens (bool). "
                 "Les listes entre crochets sont mutables et ordonnees. "
                 "Les tuples entre parentheses sont immutables. "
                 "Les dictionnaires stockent des paires cle-valeur indexees."),
                ("2. Structures conditionnelles et boucles",
                 "Les conditions s articulent autour des mots-cles if, elif et else sans parentheses obligatoires. "
                 "La boucle for s associe a l iterateur range pour parcourir des intervalles de nombres entiers. "
                 "La boucle while poursuit son execution tant qu une condition reste evaluee a vrai. "
                 "En Python, la fonction len() sur une liste renvoie le nombre d elements en complexite temporelle O(1).")
            ]
        },
        {
            "title": "Fonctions, Gestion des Exceptions et Modularite",
            "sections": [
                ("3. Conception des fonctions et arguments",
                 "Une fonction se declare avec le mot-cle def suivi de son identifiant et de parentheses. "
                 "Le mot-cle return renvoie le resultat de l evaluation vers l appelant de la routine. "
                 "Des valeurs par defaut peuvent etre assignees aux arguments optionnels lors de la definition. "
                 "Les annotations de types permettent d expliciter les signatures de maniere statique."),
                ("4. Exceptions et bibliotheque standard",
                 "La robustesse logicielle repose sur le bloc try, except et optionnellement finally pour nettoyer les ressources. "
                 "Lever une exception intentionnellement s effectue a l aide de l instruction raise. "
                 "La bibliotheque standard integre des modules cruciaux comme pathlib pour manipuler le systeme de fichiers, "
                 "json pour serialiser les flux de donnees et sys pour interagir avec l environnement d execution. "
                 "La convention PEP 8 formalise le style officiel du code Python.")
            ]
        }
    ],
    "cours_sql.pdf": [
        {
            "title": "Bases de Donnees Relationnelles et Requetes SQL",
            "sections": [
                ("1. Modele relationnel et intégrité",
                 "Une base de donnees relationnelle organise les informations sous forme de tables composees de lignes et colonnes. "
                 "La cle primaire (PRIMARY KEY) garantit l unicite de chaque enregistrement au sein d une table donnee. "
                 "La cle etrangere (FOREIGN KEY) assure l integrite referentielle entre deux tables distinctes. "
                 "Le langage SQL (Structured Query Language) permet de definir, manipuler et interroger ces structures."),
                ("2. Interrogation standard avec SELECT",
                 "La clause SELECT specifie la liste des attributs a extraire du jeu de donnees cible. "
                 "La clause FROM identifie la table source sur laquelle s applique la requete d extraction. "
                 "La clause WHERE applique un filtre precis sur les lignes avant tout traitement ulterieur. "
                 "La clause ORDER BY trie les enregistrements de maniere croissante (ASC) ou decroissante (DESC). "
                 "La clause LIMIT restreint le nombre total d enregistrements retournes au client.")
            ]
        },
        {
            "title": "Jointures, Agregations et Proprietes ACID",
            "sections": [
                ("3. Mecanismes de jointures relationnelles",
                 "Une jointure de type INNER JOIN retourne uniquement les lignes ayant une correspondance dans les deux tables participantes. "
                 "La jointure LEFT JOIN conserve l integralite des lignes de la table de gauche meme sans correspondance a droite. "
                 "La clause ON definit la condition d egalite sur laquelle repose la correlation entre les deux entites."),
                ("4. Agregations et transactions",
                 "Les fonctions d agregation COUNT, SUM, AVG, MIN et MAX calculent un resume numerique sur un ensemble de lignes. "
                 "La clause GROUP BY regroupe les enregistrements partageant une valeur commune pour l agregation. "
                 "La clause HAVING filtre les groupes ainsi constitues apres application de la fonction d agregation. "
                 "Une transaction garantit les quatre proprietes ACID : Atomicite, Coherence, Isolation et Durabilite.")
            ]
        }
    ]
}

def build_pdf(filepath: Path, pages_data: list) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=14
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=8
    )

    story = []
    for page_idx, page in enumerate(pages_data):
        if page_idx > 0:
            story.append(PageBreak())
        story.append(Paragraph(page["title"], title_style))
        story.append(Spacer(1, 10))
        for section_title, section_text in page["sections"]:
            story.append(Paragraph(section_title, heading_style))
            story.append(Paragraph(section_text, body_style))
            story.append(Spacer(1, 8))

    doc.build(story)

def verify_pdf(filepath: Path) -> bool:
    if not filepath.is_file():
        return False
    reader = PdfReader(str(filepath))
    if len(reader.pages) < 2:
        return False
    for page in reader.pages:
        text = page.extract_text()
        if not text or not text.strip():
            return False
    return True

def generate_all_pdfs(target_dir: Path = DATA_DIR) -> dict[str, bool]:
    results = {}
    for filename, pages in COURSE_DOCUMENTS.items():
        pdf_path = target_dir / filename
        build_pdf(pdf_path, pages)
        valid = verify_pdf(pdf_path)
        results[filename] = valid
    return results

def main() -> None:
    results = generate_all_pdfs(DATA_DIR)
    all_ok = True
    for filename, ok in results.items():
        if ok:
            print(f"Document genere et valide : {filename}")
        else:
            print(f"Erreur de generation pour : {filename}")
            all_ok = False
    if not all_ok:
        sys.exit(1)
    print("Tous les documents PDF ont ete generes et valides avec succes.")

if __name__ == "__main__":
    main()
