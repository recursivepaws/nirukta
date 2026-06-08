import os
from typing import List
from nirukta.models import Sloka, SutraFile
from nirukta.parsing.grammars import SUTRA_GRAMMAR
from nirukta.parsing.visitors.sloka import SlokaVisitor
from parsimonious.exceptions import ParseError


class SutraVisitor(SlokaVisitor):
    def parse(self) -> SutraFile:
        try:
            tree = SUTRA_GRAMMAR.parse(self.source)
        except ParseError as e:
            self._print_parse_error(e)
            raise
        return self.visit(tree)

    def visit_sutra(self, _, visited_children):
        citation, _, raw_slokas, _ = visited_children

        processed_slokas: List[Sloka] = []
        for sloka in raw_slokas:
            if isinstance(sloka, list):
                sloka = sloka[0]
            if isinstance(sloka, Sloka):
                processed_slokas.append(sloka)
            else:
                sloka_file = os.path.normpath(os.path.join(self.directory, sloka))
                processed_slokas.append(SlokaVisitor(sloka_file).parse().sloka)

        return SutraFile(citation, processed_slokas)

    def visit_inline_sloka(self, _, visited_children):
        _, _, _, lines, _ = visited_children
        return Sloka(list(lines))

    def visit_sloka(self, _, visited_children):
        _, citation, _, lines, _ = visited_children
        return [citation, Sloka(list(lines))]

    def visit_external_sloka(self, _, visited_children):
        _, _, _, file, _ = visited_children
        return file

    def visit_file(self, _, visited_children):
        _, file_content = visited_children
        return file_content

    def visit_file_content(self, _, visited_children):
        first, rest = visited_children
        parts = [first]
        for group in rest:
            # each group is ["/", file_part]
            _, part = group
            parts.append(part)
        return "/".join(parts)

    def visit_file_part(self, node, _):
        return node.text
