class PCLError(Exception):
    pass


class PCLWarning(Warning):
    pass


class PCLCError(PCLError):
    pass


class PCLLexerError(PCLError):
    pass


class PCLParserError(PCLError):
    pass


class PCLSemError(PCLError):
    pass


class PCLSymbolTableError(PCLSemError):
    pass


class PCLCodegenError(PCLError):
    pass
