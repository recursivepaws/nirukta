from parsimonious.grammar import Grammar

SLOKA_GRAMMAR_STR = r"""
    sloka           = ws citation_line ws line+ ws

    citation_line   = "===" ws citation_text ws "==="
    citation_text   = ~r"[^=]+"

    line            = "--- line ---" ws verse_line+
    verse_line      = !"--- line ---" token_seq ws quoted_str (ws quoted_str)* ws

    token_seq       = token (ws token)*

    token           = compound_token / simple_token / punct

    # Sandhi: one or more components joined by '+', then '=' surface form.
    # Components may themselves be parenthesised sandhi groups, enabling
    # arbitrary nesting:  (a[x]+b[y]=ab)+c[z]=abc>>abcd
    compound_token  = comp_part plus_part* "=" slp1 inflect_part*
    plus_part       = "+" comp_part
    inflect_part    = ">>" slp1
    comp_part       = paren_compound / simple_token
    paren_compound  = "(" compound_token ")"

    simple_token    = slp1 gloss*
    gloss           = trans_gloss / etym_gloss
    trans_gloss     = "[" trans_content "]"
    etym_gloss      = "{" etym_content "}"
    trans_content   = ~r"[^\]]+"
    etym_content    = ~r"[^}]+"

    # '..' must precede '.' so the longer match wins
    punct = ~r"\.+(?:\s*\d+\s*[.,;]*)?|[;,]"

    # SLP1: anything that isn't a format metacharacter or whitespace
    slp1            = ~r"[^[\]\>{}.;=+()\"\s]+"

    quoted_str      = '"' ~r'(?:[^"\\]|\\.)*' '"'
    ws              = ~r"\s*"
"""


SUTRA_GRAMMAR_STR = (
    r"""
    sutra           = citation_line ws (inline_sloka / external_sloka)+ ws
    inline_sloka    = ws "=== sloka ===" ws line+ ws
    external_sloka  = ws "=== sloka ===" ws file ws
    file            = "file:" file_content
    file_part    = ~r"[a-zA-Z0-9._]+"
    file_content = file_part ("/" file_part)+
"""
    + "\n"
    + SLOKA_GRAMMAR_STR
)

SLOKA_GRAMMAR = Grammar(SLOKA_GRAMMAR_STR)
SUTRA_GRAMMAR = Grammar(SUTRA_GRAMMAR_STR)
