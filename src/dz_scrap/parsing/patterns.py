# src/dz_scrap/parsing/patterns.py

import re

# A robust pattern to find the start of any major legal act.
DOCUMENT_START_PATTERN = re.compile(
    r'^(?:Décret|Loi|Arrêté|Décision)\s',
    re.IGNORECASE | re.MULTILINE
)

# This pattern captures the main header of a single legal document.
# It's designed to handle multi-line titles and variations in spacing.
DOCUMENT_HEADER_PATTERN = re.compile(
    r"""
    ^                                     # Start of the string (or line in multiline mode)
    (?P<type>(?:Décret|Loi|Arrêté|Décision)[\s\wéèçà\-\.\/]+?)  # Document type (non-greedy)
    \s+n°\s*(?P<number>[\d\s\-\.\/]+?)      # Document number (non-greedy)
    \s+du\s+(?P<date>.*?)                  # Date (non-greedy)
    \s+(?:portant|relative\s+au|fixant|modifiant|mettant|portant)\s+ # Action verb for the title
    (?P<title>.*?)                        # The rest of the title (non-greedy)
    # Positive lookahead: Stop matching when we see the preamble or a list of articles
    (?=
        \n\s*Le\sPrésident\sde\sla\sRépublique,|
        \n\s*Le\sPremier\sministre,|
        \n\s*Vu\s+la\s+Constitution|
        \n\s*Article\s*\d
    )
    """,
    re.VERBOSE | re.DOTALL | re.IGNORECASE | re.MULTILINE,
)

# A simpler pattern for individual decisions which often lack a detailed title.
# CHANGED: Made the title capture more greedy to grab the whole line.
INDIVIDUAL_DECISION_PATTERN = re.compile(
    r"""
    ^
    (?P<type>Décret\s(?:présidentiel|exécutif)|Arrêté) # Type of decree
    \s+du\s+(?P<date>.+?)                          # The date, non-greedy
    \s+(?P<title>(?:mettant\sfin|portant\snomination).*) # The title, now greedy to end of line
    """,
    re.VERBOSE | re.IGNORECASE | re.MULTILINE,
)


# This pattern captures individual articles within a document.
ARTICLE_PATTERN = re.compile(
    r"""
    \n\s* # Start on a new line with optional space
    (?:Art|Article)\.\s* # The literal "Art." or "Article."
    (?P<number>[\w\d]+(?:er)?)          # Article number (e.g., "1er", "2", "15bis")
    \s*[—\-]?\s* # Optional dash or em-dash after the number
    (?P<content>.*?)                    # The content of the article (non-greedy)
    # Positive lookahead: Stop when we see the next article, a closing statement,
    # or the end of the document.
    (?=
        \n\s*(?:Art|Article)\.|
        \n\s*Fait\sà\sAlger|
        \n\s*Le\sministre|
        \n\s*Par\s+ces\s+motifs|
        $
    )
    """,
    re.VERBOSE | re.DOTALL,
)
