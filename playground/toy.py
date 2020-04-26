from sly import Lexer, Parser
from ctypes import CFUNCTYPE, c_double
from llvmlite import ir, binding
import os


class ToyLexer(Lexer):
    tokens = {NUMBER, PLUS, MINUS, TIMES, DIVIDE, COMMENT, PRINT}

    # PCL Multiline comment
    COMMENT = r'(?s)\(\*.*?\*\)'

    ignore = r' \t'

    NUMBER = r'\d+'
    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    PRINT = r'print'

    ignore_newline = '\n+'

    def COMMENT(self, t):
        self.lineno += t.value.count('\n')
        return None

    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        print(
            'Illegal character {} at line {}'.format(
                t.value[0],
                self.lineno))
        self.index += 1


class Constant:

    def __init__(self, value, builder, module):
        self.builder = builder
        self.module = module
        self.value = int(value)

    def eval(self):
        return self.value

    def sem(self):
        # infers type of node
        self.typ = int

    def codegen(self):
        i = ir.Constant(ir.IntType(8), self.value)
        return i


class BinOp:

    def __init__(self, op, lhs, rhs, builder, module):
        self.builder = builder
        self.module = module
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def eval(self):
        if self.op == '+':
            return self.lhs.eval() + self.rhs.eval()
        if self.op == '-':
            return self.lhs.eval() - self.rhs.eval()
        if self.op == '*':
            return self.lhs.eval() * self.rhs.eval()
        if self.op == '/':
            return self.lhs.eval() // self.rhs.eval()

    def codegen(self):
        if self.op == '+':
            i = self.builder.add(self.lhs.codegen(), self.rhs.codegen())
        elif self.op == '-':
            i = self.builder.sub(self.lhs.codegen(), self.rhs.codegen())
        elif self.op == '*':
            i = self.builder.mul(self.lhs.codegen(), self.rhs.codegen())
        elif self.op == '/':
            i = self.builder.udiv(self.lhs.codegen(), self.rhs.codegen())

        return i


class Print:

    def __init__(self, value, builder, module, printf, printf_counter):
        self.builder = builder
        self.module = module
        self.printf = printf
        self.value = value
        self.printf_counter = printf_counter

    def eval(self):
        print(self.value.eval())

    def codegen(self):
        value = self.value.codegen()

        # Declare argument list
        voidptr_ty = ir.IntType(8).as_pointer()
        fmt = "%i\n\0"
        c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                            bytearray(fmt.encode("utf8")))
        global_fmt = ir.GlobalVariable(
            self.module, c_fmt.type, name="fstr{}".format(
                self.printf_counter))
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt
        fmt_arg = self.builder.bitcast(global_fmt, voidptr_ty)
        # Call Print Function
        return self.builder.call(self.printf, [fmt_arg, value])


class Program:

    def __init__(self, stmt_list):
        self.stmt_list = stmt_list

    def eval(self):
        for stmt in self.stmt_list:
            stmt.eval()

    def codegen(self):
        for stmt in self.stmt_list:
            stmt.codegen()


class ToyParser(Parser):

    def __init__(self, module, builder, printf):
        self.module = module
        self.builder = builder
        self.printf = printf
        self.printf_counter = -1

    tokens = ToyLexer.tokens

    # prosetaistikotika + proteraiotita. Going down -> increases priority.
    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE')
    )

    # program = stmt_list
    @_('stmt_list')
    def program(self, p):
        return Program(p.stmt_list)

    # stmt_list := stmt_list stmt
    # Base of recursion
    @_('stmt')
    def stmt_list(self, p):
        return [p.stmt]

    # Recursion
    @_('stmt_list stmt')
    def stmt_list(self, p):
        # Attempt to use mutable operations
        p.stmt_list.append(p.stmt)
        return p.stmt_list

    @_('expr')
    def stmt(self, p):
        return p.expr

    @_('PRINT expr')
    def stmt(self, p):
        self.printf_counter += 1
        return Print(
            p.expr,
            self.builder,
            self.module,
            self.printf,
            self.printf_counter)

    @_('"(" expr ")"')
    def expr(self, p):
        return p.expr

    @_('expr PLUS expr', 'expr MINUS expr',
       'expr TIMES expr', 'expr DIVIDE expr')
    def expr(self, p):
        return BinOp(p[1], p.expr0, p.expr1, self.builder, self.module)

    @_('NUMBER')
    def expr(self, p):
        return Constant(p.NUMBER, self.builder, self.module)


class ToyCodeGen:

    def __init__(self):
        self.binding = binding
        self.binding.initialize()
        self.binding.initialize_native_target()
        self.binding.initialize_native_asmprinter()
        self._config_llvm()
        self._create_execution_engine()
        self._declare_print_function()

    def _config_llvm(self):
        self.module = ir.Module(name='example')
        self.module.triple = self.binding.get_default_triple()
        func_type = ir.FunctionType(ir.VoidType(), [], False)
        base_func = ir.Function(self.module, func_type, name="main")
        block = base_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)

    def _create_execution_engine(self):
        """
        Create an ExecutionEngine suitable for JIT code generation on
        the host CPU.  The engine is reusable for an arbitrary number of
        modules.
        """
        target = self.binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        # And an execution engine with an empty backing module
        backing_mod = binding.parse_assembly("")
        engine = binding.create_mcjit_compiler(backing_mod, target_machine)
        self.engine = engine

    def _declare_print_function(self):
        # Declare Printf function
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        printf = ir.Function(self.module, printf_ty, name="printf")
        self.printf = printf

    def _compile_ir(self):
        """
        Compile the LLVM IR string with the given engine.
        The compiled module object is returned.
        """
        # Create a LLVM module object from the IR
        self.builder.ret_void()
        llvm_ir = str(self.module)
        mod = self.binding.parse_assembly(llvm_ir)
        mod.verify()
        # Now add the module and make sure it is ready for execution
        self.engine.add_module(mod)
        self.engine.finalize_object()
        self.engine.run_static_constructors()
        return mod

    def _optimize_ir(self):
        self.module_ref = binding.parse_assembly(str(self.module))
        self.module_pass_manager = binding.ModulePassManager()
        self.module_pass_manager.run(self.module_ref)

    def create_ir(self):
        self._compile_ir()
        self._optimize_ir()

    def generate_outputs(self, filename):
        final_code = str(self.module)
        llvm_filename = filename + '.ll'
        obj_filename = filename + '.o'
        output_filename = filename + '.out'

        with open(llvm_filename, 'w+') as f:
            f.write(final_code)

        os.system('llc-8 -filetype=obj {}'.format(llvm_filename))
        os.system('gcc {} -o {}'.format(obj_filename, output_filename))


if __name__ == '__main__':
    s = '''print 2
           print 3
    '''
    toy_lexer = ToyLexer()
    lex_result = toy_lexer.tokenize(s)

    toy_codegen = ToyCodeGen()

    toy_parser = ToyParser(
        toy_codegen.module,
        toy_codegen.builder,
        toy_codegen.printf)

    # Returns root of AST
    parse_result = toy_parser.parse(lex_result)

    print('Interpreted')

    parse_result.eval()

    print('LLVM Code')

    parse_result.codegen()
    toy_codegen.create_ir()
    print(str(toy_codegen.module))

    toy_codegen.generate_outputs('toy')
