"""
Validates a user entered pattern against STIXPattern grammar.
"""

from antlr4 import CommonTokenStream, ParseTreeWalker

from . import object_validator
from ..exceptions import STIXPatternErrorListener
from .grammars.STIXPatternLexer import STIXPatternLexer
from .grammars.STIXPatternParser import STIXPatternParser
from .inspector import InspectionListener


def run_validator(pattern, start):
    """
    Validates a pattern against the STIX Pattern grammar.  Error messages are
    returned in a list.  The test passed if the returned list is empty.
    """
    parseErrListener = STIXPatternErrorListener()

    lexer = STIXPatternLexer(pattern)
    # it always adds a console listener by default... remove it.
    lexer.removeErrorListeners()

    stream = CommonTokenStream(lexer)

    parser = STIXPatternParser(stream)

    # it always adds a console listener by default... remove it.
    parser.removeErrorListeners()
    parser.addErrorListener(parseErrListener)

    # To improve error messages, replace "<INVALID>" in the literal
    # names with symbolic names.  This is a hack, but seemed like
    # the simplest workaround.
    for i, lit_name in enumerate(parser.literalNames):
        if lit_name == u"<INVALID>":
            parser.literalNames[i] = parser.symbolicNames[i]

    tree = parser.pattern()
    inspection_listener = InspectionListener()

    # replace with easier-to-understand error message
    if not (start[0] == '[' or start == '(['):
        parseErrListener.err_strings.insert(0, "FAIL: Error found at line 1:0. "
                                               "input is missing square brackets")

    # validate observed objects
    if len(parseErrListener.err_strings) == 0:
        ParseTreeWalker.DEFAULT.walk(inspection_listener, tree)
        patt_data = inspection_listener.pattern_data()

        # check objects
        obj_validator_results = object_validator.verify_object(patt_data)
        if obj_validator_results:
            parseErrListener.err_strings.extend(obj_validator_results)

        # check qualifiers
        qualifiers = [q.split()[0] for q in patt_data.qualifiers]
        if len(qualifiers) != len(set(qualifiers)):
            parseErrListener.err_strings.insert(0, "FAIL: The same qualifier is"
                                                   " used more than once")

    return parseErrListener.err_strings
