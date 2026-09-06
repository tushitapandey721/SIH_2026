"""Legal query normalization and semantic expansion for IP-SAKTI Sahayak."""

import re
from typing import Tuple, List


# Statutory normalization patterns
SECTION_SUB_NESTED_RE = re.compile(r"(?i)\b(?:sec(?:tion)?\.?\s*)?(\d+)\s*\(([0-9]+)\)\s*\(([a-z0-9]+)\)", re.IGNORECASE)
SECTION_SUBCLAUSE_RE = re.compile(r"(?i)\b(?:sec(?:tion)?\.?\s*)?(\d+)\s*\(([a-z0-9]+)\)", re.IGNORECASE)
RULE_SUB_RE = re.compile(r"(?i)\b(?:rule\.?\s*)?(\d+)\s*[-_ ]\s*([a-z0-9]+)\b", re.IGNORECASE)
ARTICLE_RE = re.compile(r"(?i)\b(?:art(?:icle)?\.?\s*)(\d+[A-Za-z]?)\b", re.IGNORECASE)
HYPHENATED_SECTION_RE = re.compile(r"(?i)\b(\d+)\s*[-_]\s*([a-z0-9]+)\b", re.IGNORECASE)

# Legal domain concept mappings (general domain synonyms across statutory areas)
LEGAL_CONCEPT_EXPANSIONS = [
    # 1. Patents Act Section 2 Definitions & Patentability Criteria
    (
        re.compile(r"(?i)\b(inventive\s+step|technical\s+advance|non[\s-]obvious)\b"),
        "Section 2(1)(ja) inventive step technical advance economic significance not obvious",
    ),
    (
        re.compile(r"(?i)\b(patentab(?:ility|le)|patent\s+criteria|qualif(?:y|ies|ied)\s+as\s+(?:an\s+)?(?:new\s+)?invention|definition\s+of\s+invention|what\s+(?:is|qualifies\s+as)\s+(?:an?\s+)?(?:new\s+)?invention)\b"),
        "Section 2(1)(j) Section 2(1)(ja) Section 2(1)(l) invention new product process capable of industrial application not anticipated",
    ),
    (
        re.compile(r"(?i)\b(new\s+invention|prior\s+art|anticipated\s+by\s+publication|state\s+of\s+the\s+art|public\s+domain)\b"),
        "Section 2(1)(l) new invention not anticipated publication public domain state of the art",
    ),
    (
        re.compile(r"(?i)\b(pharmaceutical\s+substance)\b"),
        "Section 2(1)(ta) pharmaceutical substance new entity inventive steps",
    ),
    (
        re.compile(r"(?i)\b(capable\s+of\s+industrial\s+application|industrial\s+applicability)\b"),
        "Section 2(1)(ac) capable of industrial application made or used in industry",
    ),

    # 2. Synthetic Derivatives, Modified Compounds vs Traditional Knowledge (Distinguishing 2(1)(j), 2(1)(ja), 3(d), 3(p))
    (
        re.compile(r"(?i)\b(synthetic\s+(?:derivative|modification|substance|compound)|structurally\s+modified|chemically\s+modified|isolated\s+active\s+(?:compound|moiety|fraction|alkaloid|molecule)|plant[\s-]derived\s+(?:chemical|compound|molecule|alkaloid|substance)|derivative\s+of\s+(?:a\s+)?(?:chemical\s+compound|naturally\s+occurring|plant|substance)|novel\s+chemical\s+(?:compound|substance)|modified\s+(?:active\s+)?(?:molecule|moiety|substance|compound))\b"),
        "Section 2(1)(j) Section 2(1)(ja) Section 3(d) Patents Act invention new product process inventive step technical advance enhanced efficacy derivative known substance",
    ),
    (
        re.compile(r"(?i)\b(enhanced\s+efficacy|new\s+form\s+of\s+known\s+substance|therapeutic\s+efficacy|differ\s+significantly\s+in\s+properties|derivative\s+of\s+known\s+substance)\b"),
        "Section 3(d) known substance enhanced efficacy therapeutic efficacy not patentable unless significant enhancement derivative",
    ),
    (
        re.compile(r"(?i)\b(mere\s+admixture|admixture\s+resulting\s+only\s+in\s+aggregation)\b"),
        "Section 3(e) substance obtained by admixture aggregation of properties not patentable",
    ),
    (
        re.compile(r"(?i)\b(traditional\s+(?:knowledge|herbal|medicinal|remedy|medicine|formulation|recipe|practice)|botanical\s+knowledge|classical(?:\s+\w+){0,4}\s+(?:formulation|remedy|medicine|drug|preparation|churna|rasayana|oil|recipe|taila|avaleha|kwatha|ghrita|ayurvedic)|ayurvedic(?:\s+\w+){0,4}\s+(?:formulation|remedy|medicine|recipe|preparation|polyherbal)|polyherbal(?:\s+\w+){0,4}\s+(?:formulation|composition|mixture|medicine|preparation|remedy)|known\s+ayurvedic|old\s+ayurvedic|unmodified\s+(?:classical|ayurvedic|herbal)|exclude\s+traditional\s+medicinal|known\s+properties\s+of\s+(?:traditionally|ayurvedic|plants?)|triphala|chyawanprash|churna|ghrita|taila|asava|arishta|bhasma|rasayana|grandmother|ancestral\s+recipe|family\s+recipe)\b"),
        "Section 3(p) Section 3(e) Patents Act traditional knowledge not patentable aggregation duplication known properties traditionally known component mere admixture",
    ),
    (
        re.compile(r"(?i)\b(prohibit(?:s|ed|ing|ion)?|banned|forbidden|not\s+patentable|excluded\s+from\s+patentability|inventions\s+not\s+patentable|what\s+are\s+not\s+inventions)\b"),
        "Section 3 Patents Act not patentable excluded from patentability traditional knowledge known properties mere admixture",
    ),

    # 3. AYUSH Drug Licensing & Labelling (D&C Act & Rules)
    (
        re.compile(r"(?i)\b(rule\s+161|labelling\s+requirements|label(?:s|ling)?\s+(?:for|of)\s+ayurvedic|particulars\s+(?:displayed\s+on\s+label|on\s+container)|botanical\s+names\s+of\s+ingredients|true\s+list\s+of\s+ingredients)\b"),
        "Rule 161 Rule 161A Part XVII Drugs and Cosmetics Rules labelling packing particulars ingredients botanical names container Ayurvedic Siddha Unani",
    ),
    (
        re.compile(r"(?i)\b(rule\s+158b?|difference\s+between\s+classical\s+and\s+proprietary|licens(?:e|ing)\s+requirements|asu\s+drug\s+licen[sc]e|manufacturing\s+licen[sc]e|drug\s+licen[sc]e|first\s+schedule\s+books)\b"),
        "Rule 158B First Schedule authoritative books classical formulation patent or proprietary ASU medicine Section 3(h)",
    ),
    (
        re.compile(r"(?i)\b(adulterated\s+ayurvedic|penalties\s+for\s+adulterated|spurious\s+ayurvedic)\b"),
        "Section 33EEC Section 33EE adulterated drugs penalties Ayurvedic ASU",
    ),
    (
        re.compile(r"(?i)\b(phytopharmaceutical\s+drugs?|clinical\s+trials?\s+phytopharmaceutical|purified\s+fraction)\b"),
        "Phytopharmaceutical Drugs Guidance clinical trials safety data purified fraction novel drug",
    ),

    # 4. Biological Diversity & Access Benefit Sharing (BDA 2002 / 2023)
    (
        re.compile(r"(?i)\b(national\s+biodiversity\s+authority|nba\s+approval|patent\s+under\s+section\s+6|patent\s+application\s+biological\s+resource)\b"),
        "Section 6 Section 19 Biological Diversity Act prior approval National Biodiversity Authority patent application",
    ),
    (
        re.compile(r"(?i)\b(foreign\s+persons?\s+accessing|foreign\s+entity\s+biological\s+resource|prior\s+approval\s+section\s+3)\b"),
        "Section 3 Biological Diversity Act prior approval foreign persons commercial utilization",
    ),
    (
        re.compile(r"(?i)\b(state\s+biodiversity\s+board|sbb\s+notification|notify\s+state\s+biodiversity|collecting\s+medicinal\s+herbs|vaids?\s+(?:and\s+)?hakims?|traditional\s+practitioners?\s+exempt)\b"),
        "Section 7 Section 3 Biological Diversity Act prior intimation State Biodiversity Board vaids hakims local people exempt",
    ),

    # 5. International Treaties (Nagoya Protocol, TRIPS, PCT, WIPO GRATK, CBD)
    (
        re.compile(r"(?i)\b(article\s+6\b|access\s+to\s+genetic\s+resources|pic|prior\s+informed\s+consent|mutually\s+agreed\s+terms|mat|nagoya\s+protocol|nagoya)\b"),
        "Article 6 Article 5 Article 7 Nagoya Protocol Access to Genetic Resources Prior Informed Consent PIC Mutually Agreed Terms MAT benefit-sharing sovereign rights",
    ),
    (
        re.compile(r"(?i)\b(trips|trips\s+agreement|article\s+27|patentable\s+subject\s+matter|plant\s+varieties|micro[\s-]organisms?|sui\s+generis)\b"),
        "Article 27 Article 27(1) Article 27(3)(b) TRIPS Agreement patentable subject matter novelty inventive step micro-organisms plant varieties sui generis",
    ),
    (
        re.compile(r"(?i)\b(pct|patent\s+cooperation\s+treaty|claiming\s+priority|priority\s+claim|international\s+application|pct\s+article\s+8|international\s+search\s+report)\b"),
        "Article 8 Article 11 Article 19 PCT Treaty Claiming Priority international application filing date time limit Paris Convention",
    ),
    (
        re.compile(r"(?i)\b(mandatory\s+disclosure|wipo|gratk|genetic\s+resources\s+and\s+associated\s+traditional\s+knowledge|country\s+of\s+origin\s+disclosure|gratk\s+article\s+3|disclosure\s+requirements?)\b"),
        "Article 3 Article 4 Article 5 WIPO GRATK Treaty mandatory disclosure requirement country of origin source genetic resources traditional knowledge patent application",
    ),
    (
        re.compile(r"(?i)\b(cbd|convention\s+on\s+biological\s+diversity|sovereign\s+rights|fair\s+benefit\s+sharing|cbd\s+article\s+15|ex[\s-]situ\s+conservation|in[\s-]situ\s+conservation)\b"),
        "Article 15 Article 8(j) Article 19 Convention on Biological Diversity CBD sovereign rights Access to Genetic Resources prior informed consent fair and equitable sharing of benefits",
    ),

    # 6. Trade Marks, Geographical Indications, and Advertising
    (
        re.compile(r"(?i)\b(absolute\s+grounds|grounds\s+for\s+refusal|trademark\s+registration|brand\s+name\s+trademark|logo\s+trademark)\b"),
        "Section 9 Section 11 Trade Marks Act absolute grounds refusal distinctiveness descriptive marks",
    ),
    (
        re.compile(r"(?i)\b(geographical\s+indication|gi\s+act|geographical\s+origin|place\s+of\s+origin|regional\s+origin|agricultural\s+(?:goods|products?|crops?|produce)|natural\s+goods|reputation\s+(?:attributable|comes\s+from|linked\s+to)\s+(?:origin|place)|appellation\s+of\s+origin|indication\s+associated\s+with\s+(?:a\s+)?territory|products\s+whose\s+reputation\s+comes\s+from|protects?\s+(?:products|goods)\s+whose\s+reputation)\b"),
        "Section 2(1)(e) Section 2(1)(f) Section 8 Section 11 Geographical Indications Act geographical indication agricultural goods natural goods territory region locality place of origin reputation quality characteristics registration",
    ),
    (
        re.compile(r"(?i)\b(section\s+8\s+of\s+the\s+(?:gi|geographical)|who\s+can\s+apply\s+(?:for\s+)?(?:registration\s+of\s+)?gi|apply\s+for\s+(?:a\s+)?geographical\s+indication|registration\s+to\s+be\s+in\s+respect\s+of\s+particular\s+goods|authorised\s+user\s+of\s+a\s+registered\s+geographical)\b"),
        "Section 8 Section 11 Section 17 Geographical Indications Act registration to be in respect of particular goods and area class of goods territory region locality association of persons producers authorised user",
    ),
    (
        re.compile(r"(?i)\b(authori[sz]ed\s+user|registration\s+of\s+authori[sz]ed\s+user)\b"),
        "Section 17 Section 2(1)(b) Section 8 Geographical Indications Act authorised user registration registered proprietor",
    ),
    (
        re.compile(r"(?i)\b(misleading\s+advertisements?|miraculous\s+cures|magic\s+remedies|false\s+claims\s+ayurvedic)\b"),
        "Section 3 Section 4 Section 5 Drugs and Magic Remedies Act prohibition misleading advertisements magic remedies",
    ),
]


def normalize_statutory_identifiers(query: str) -> str:
    """Normalizes statutory citations in queries to canonical legal formats."""
    # 1. Normalize Section 2(1)(ja), 2(1)(j), 2(1)(l), 2(1)(ta)
    normalized = SECTION_SUB_NESTED_RE.sub(r"Section \1(\2)(\3)", query)

    # 2. Normalize 3(p), 3 (p), sec 3(p) -> Section 3(p)
    normalized = SECTION_SUBCLAUSE_RE.sub(r"Section \1(\2)", normalized)

    # 3. Normalize Rule 158-B, 158 - B, rule 158-B -> Rule 158B
    normalized = RULE_SUB_RE.sub(r"Rule \1\2", normalized)

    # 4. Normalize Article 6, Art. 6 -> Article 6
    normalized = ARTICLE_RE.sub(r"Article \1", normalized)

    # 5. Normalize 33-EEC -> 33EEC
    normalized = HYPHENATED_SECTION_RE.sub(r"\1\2", normalized)

    return normalized.strip()


def expand_legal_query(query: str) -> Tuple[str, str]:
    """Applies canonical normalization and semantic legal expansion.

    Returns:
        Tuple of (normalized_query, expanded_query_for_bm25_and_dense).
    """
    normalized = normalize_statutory_identifiers(query)

    added_terms: List[str] = []
    for pattern, expansion in LEGAL_CONCEPT_EXPANSIONS:
        if pattern.search(normalized):
            added_terms.append(expansion)

    if added_terms:
        expansion_text = " ".join(added_terms)
        expanded = f"{normalized} {expansion_text}".strip()
    else:
        expanded = normalized

    return normalized, expanded
