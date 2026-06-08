from typing import Union

from nirukta.models.tokens.compound import CompoundToken, SoundChangeToken
from nirukta.models.tokens.punctuation import PunctuationToken
from nirukta.models.tokens.simple import SimpleToken


type TokenType = Union[PunctuationToken, SimpleToken, SoundChangeToken, CompoundToken]
