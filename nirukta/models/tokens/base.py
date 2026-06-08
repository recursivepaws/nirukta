from typing import Union
from nirukta.models.tokens.punctuation import PunctuationToken
from nirukta.models.tokens.simple import SimpleToken
from nirukta.models.tokens.compound import SoundChangeToken, CompoundToken


type TokenType = Union[PunctuationToken, SimpleToken, SoundChangeToken, CompoundToken]
