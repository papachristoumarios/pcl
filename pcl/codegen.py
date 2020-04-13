from ctypes import CFUNCTYPE, c_double
from llvmlite import ir, binding
from pcl.error import PCLCodegenError
import os

class LLVMTypeSize:
    T_BOOL = 1
    T_CHAR = 1
    T_REAL = 10
    T_PTR = 2
    T_INT = 8

    @staticmethod
    def get_const_array_size(n, t):
        if n <= 0:
            raise PCLCodegenError('Allocating array with non-positive number of elements')
        return n * t.value

class LLVMTypes:
    T_INT = ir.IntType(LLVMTypeSize.T_INT)
    T_BOOL = ir.IntType(LLVMTypeSize.T_BOOL)
    T_CHAR = ir.IntType(LLVMTypeSize.T_CHAR)
    T_PROC = ir.VoidType()
    T_PTR = ir.PointerType(LLVMTypeSize.T_PTR)
    T_REAL = ir.DoubleType()

    mapping = {
        'integer' : T_INT,
        'bool' : T_BOOL,
        'real' : T_REAL,
        'char' : T_CHAR
    }

class LLVMConstants:
    ZERO_INT = ir.Constant(LLVMTypes.T_INT, 0)
    ZERO_REAL = ir.Constant(LLVMTypes.T_REAL, 0)

class LLVMOperators:

    # Accessible with comp_mapping.get(x, x)
    comp_mapping = {
        '=' : '==',
        '<>' : '!=',
    }

    @staticmethod
    def get_op(op):
        return LLVMOperators.comp_mapping.get(op, op)


class PCLCodegen:

    def __init__(self):
        self.binding = binding
        self.binding.initialize()
        self.binding.initialize_native_target()
        self.binding.initialize_native_asmprinter()
        self._config_llvm()
        self._create_execution_engine()
        self._declare_printf()
        self._declare_scanf()

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

    def _declare_printf(self):
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")

    def _declare_scanf(self):
        voidptr_ty = ir.IntType(8).as_pointer()
        scanf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        self.scanf = ir.Function(self.module, scanf_ty, name="scanf")

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

    def generate_outputs(self, filename):
        self._compile_ir()
        final_code = str(self.module)
        llvm_filename = filename + '.ll'
        obj_filename = filename + '.o'
        output_filename = filename + '.out'

        with open(llvm_filename, 'w+') as f:
            f.write(final_code)

        os.system('llc-8 -filetype=obj {}'.format(llvm_filename))
        os.system('gcc {} -o {}'.format(obj_filename, output_filename))
