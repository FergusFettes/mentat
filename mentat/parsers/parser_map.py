from mentat.parsers.block_parser import BlockParser
from mentat.parsers.json_parser import JsonParser
from mentat.parsers.parser import Parser
from mentat.parsers.replacement_parser import ReplacementParser
from mentat.parsers.unified_diff_parser import UnifiedDiffParser

parser_map: dict[str, Parser] = {
    "block": BlockParser(),
    "replacement": ReplacementParser(),
    "unified-diff": UnifiedDiffParser(),
    # JsonParser is experimental and has no streaming or tests; don't use it yet!
    "json": JsonParser(),
}
