from enum import Enum
from typing import Optional
from dataclasses import dataclass

# Enumerations for grammatical categories


class PartOfSpeech(Enum):
    NOUN = "noun"
    PRONOUN = "pronoun"
    ADJECTIVE = "adjective"
    VERB = "verb"
    PARTICIPLE = "participle"
    INDECLINABLE = "indeclinable"
    COMPOUND = "compound"


class Gender(Enum):
    MASCULINE = "masculine"
    FEMININE = "feminine"
    NEUTER = "neuter"


class Number(Enum):
    SINGULAR = "singular"
    DUAL = "dual"
    PLURAL = "plural"


class Case(Enum):
    NOMINATIVE = "nominative"
    ACCUSATIVE = "accusative"
    INSTRUMENTAL = "instrumental"
    DATIVE = "dative"
    ABLATIVE = "ablative"
    GENITIVE = "genitive"
    LOCATIVE = "locative"
    VOCATIVE = "vocative"

    @classmethod
    def parse(cls, text: str) -> "Case":
        case_map = {
            "NOM": Case.NOMINATIVE,
            "ACC": Case.ACCUSATIVE,
            "INS": Case.INSTRUMENTAL,
            "DAT": Case.DATIVE,
            "ABL": Case.ABLATIVE,
            "GEN": Case.GENITIVE,
            "LOC": Case.LOCATIVE,
            "VOC": Case.VOCATIVE,
        }
        return case_map[text]


class Person(Enum):
    FIRST = "first"
    SECOND = "second"
    THIRD = "third"


class Tense(Enum):
    PRESENT = "present"
    IMPERFECT = "imperfect"
    PERFECT = "perfect"
    AORIST = "aorist"
    FUTURE = "future"
    CONDITIONAL = "conditional"
    IMPERATIVE = "imperative"
    OPTATIVE = "optative"
    BENEDICTIVE = "benedictive"


class Voice(Enum):
    PARASMAIPADA = "parasmaipada"
    ATMANEPADA = "atmanepada"
    PASSIVE = "passive"


class ParticipleType(Enum):
    PRESENT_ACTIVE = "present_active"
    PRESENT_MIDDLE = "present_middle"
    PAST_PASSIVE = "past_passive"
    PAST_ACTIVE = "past_active"
    FUTURE_ACTIVE = "future_active"
    GERUNDIVE = "gerundive"
    ABSOLUTIVE = "absolutive"


class CompoundType(Enum):
    TATPURUSHA = "tatpurusha"
    BAHUVRIHI = "bahuvrihi"
    DVANDVA = "dvandva"
    KARMADHARAYA = "karmadharaya"
    AVYAYIBHAVA = "avyayibhava"
    DVIGU = "dvigu"


@dataclass
class SanskritInflection:
    """
    Represents the grammatical inflection of a Sanskrit word.
    The actual word form is stored separately.
    """

    pos: PartOfSpeech

    # Nominal features (nouns, pronouns, adjectives, participles)
    gender: Optional[Gender] = None
    number: Optional[Number] = None
    case: Optional[Case] = None

    # Verbal features
    person: Optional[Person] = None
    tense: Optional[Tense] = None
    voice: Optional[Voice] = None

    # Participle features
    participle_type: Optional[ParticipleType] = None

    # Compound features
    compound_type: Optional[CompoundType] = None
    compound_components: Optional[list] = None

    # Additional information

    # Base stem form
    stem: Optional[str] = None

    # Verbal root (dhatu)
    root: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate the inflection based on part of speech"""
        if self.pos in [
            PartOfSpeech.NOUN,
            PartOfSpeech.PRONOUN,
            PartOfSpeech.ADJECTIVE,
        ]:
            if self.gender is None or self.number is None or self.case is None:
                raise ValueError(f"{self.pos.value} requires gender, number, and case")

        elif self.pos == PartOfSpeech.VERB:
            if (
                self.person is None
                or self.number is None
                or self.tense is None
                or self.voice is None
            ):
                raise ValueError("Verb requires person, number, tense, and voice")

        elif self.pos == PartOfSpeech.PARTICIPLE:
            if (
                self.participle_type is None
                or self.gender is None
                or self.number is None
                or self.case is None
            ):
                raise ValueError("Participle requires type, gender, number, and case")

    def is_nominal(self) -> bool:
        """Check if this is a nominal form (has case declension)"""
        return self.pos in [
            PartOfSpeech.NOUN,
            PartOfSpeech.PRONOUN,
            PartOfSpeech.ADJECTIVE,
            PartOfSpeech.PARTICIPLE,
        ]

    def is_verbal(self) -> bool:
        """Check if this is a finite verbal form"""
        return self.pos == PartOfSpeech.VERB

    def agrees_with(self, other: "SanskritInflection") -> bool:
        """Check if this inflection agrees with another (for adjective-noun agreement)"""
        if not (self.is_nominal() and other.is_nominal()):
            return False
        return (
            self.gender == other.gender
            and self.number == other.number
            and self.case == other.case
        )

    def __str__(self) -> str:
        """Human-readable representation"""
        parts = [self.pos.value]

        if self.is_nominal():
            parts.extend(
                [
                    self.gender.value if self.gender else "?",
                    self.number.value if self.number else "?",
                    self.case.value if self.case else "?",
                ]
            )

        if self.is_verbal():
            parts.extend(
                [
                    f"{self.person.value if self.person else '?'} person",
                    self.number.value if self.number else "?",
                    self.tense.value if self.tense else "?",
                    self.voice.value if self.voice else "?",
                ]
            )

        if self.participle_type:
            parts.append(self.participle_type.value)

        if self.compound_type:
            parts.append(f"({self.compound_type.value} compound)")

        return ", ".join(parts)

    @classmethod
    def parse(cls, notation: str, **kwargs) -> "SanskritInflection":
        """
        Parse compact notation like:
        - "V.1.SG.PRES.ATM" (verb, 1st person, singular, present, atmanepada)
        - "N.M.DU.NOM" (noun, masculine, dual, nominative)
        - "PTCP.PPP.M.DU.NOM" (participle, past passive, masc, dual, nom)
        - "IND" (indeclinable)
        - "COMP.DVANDVA.M.DU.ACC" (compound)
        """
        parts = notation.upper().split(".")

        # Mapping shortcuts to enums
        pos_map = {
            "V": PartOfSpeech.VERB,
            "N": PartOfSpeech.NOUN,
            "ADJ": PartOfSpeech.ADJECTIVE,
            "PRON": PartOfSpeech.PRONOUN,
            "PTCP": PartOfSpeech.PARTICIPLE,
            "IND": PartOfSpeech.INDECLINABLE,
            "COMP": PartOfSpeech.COMPOUND,
        }

        gender_map = {"M": Gender.MASCULINE, "F": Gender.FEMININE, "N": Gender.NEUTER}
        number_map = {"SG": Number.SINGULAR, "DU": Number.DUAL, "PL": Number.PLURAL}
        # case_map = {
        #     "NOM": Case.NOMINATIVE,
        #     "ACC": Case.ACCUSATIVE,
        #     "INS": Case.INSTRUMENTAL,
        #     "DAT": Case.DATIVE,
        #     "ABL": Case.ABLATIVE,
        #     "GEN": Case.GENITIVE,
        #     "LOC": Case.LOCATIVE,
        #     "VOC": Case.VOCATIVE,
        # }
        person_map = {"1": Person.FIRST, "2": Person.SECOND, "3": Person.THIRD}
        tense_map = {
            "PRES": Tense.PRESENT,
            "IMPF": Tense.IMPERFECT,
            "PERF": Tense.PERFECT,
            "AOR": Tense.AORIST,
            "FUT": Tense.FUTURE,
            "COND": Tense.CONDITIONAL,
            "IMP": Tense.IMPERATIVE,
            "OPT": Tense.OPTATIVE,
        }
        voice_map = {
            "PAR": Voice.PARASMAIPADA,
            "ATM": Voice.ATMANEPADA,
            "PASS": Voice.PASSIVE,
        }
        ptcp_map = {
            "PRP": ParticipleType.PRESENT_ACTIVE,
            "PRM": ParticipleType.PRESENT_MIDDLE,
            "PPP": ParticipleType.PAST_PASSIVE,
            "PPA": ParticipleType.PAST_ACTIVE,
            "FUT": ParticipleType.FUTURE_ACTIVE,
            "GRD": ParticipleType.GERUNDIVE,
            "ABS": ParticipleType.ABSOLUTIVE,
        }
        compound_map = {
            "TP": CompoundType.TATPURUSHA,
            "BV": CompoundType.BAHUVRIHI,
            "DV": CompoundType.DVANDVA,
            "KD": CompoundType.KARMADHARAYA,
            "AV": CompoundType.AVYAYIBHAVA,
            "DG": CompoundType.DVIGU,
        }

        pos = pos_map[parts[0]]

        if pos == PartOfSpeech.INDECLINABLE:
            return cls(pos=pos, **kwargs)

        # Parse based on part of speech
        if pos == PartOfSpeech.VERB:
            return cls(
                pos=pos,
                person=person_map[parts[1]],
                number=number_map[parts[2]],
                tense=tense_map[parts[3]],
                voice=voice_map[parts[4]],
                **kwargs,
            )

        elif pos == PartOfSpeech.PARTICIPLE:
            return cls(
                pos=pos,
                participle_type=ptcp_map[parts[1]],
                gender=gender_map[parts[2]],
                number=number_map[parts[3]],
                case=Case.parse(parts[4]),
                **kwargs,
            )

        elif pos == PartOfSpeech.COMPOUND:
            return cls(
                pos=pos,
                compound_type=compound_map[parts[1]],
                gender=gender_map[parts[2]],
                number=number_map[parts[3]],
                case=Case.parse(parts[4]),
                **kwargs,
            )

        else:  # Noun, Pronoun, Adjective
            return cls(
                pos=pos,
                gender=gender_map[parts[1]],
                number=number_map[parts[2]],
                case=Case.parse(parts[3]),
                **kwargs,
            )
