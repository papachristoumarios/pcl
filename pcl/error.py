class PCLError(Exception):
    pass

class PCLCError(PCLError):
    pass

class PCLLexerError(PCLError):
    pass

class PCLParserError(PCLError):
    pass

class PCLSymbolTableError(PCLError):
    pass
