from ctypes import CFUNCTYPE, c_double
from llvmlite import ir, binding
from pcl.error import PCLCodegenError
import os
from subprocess import check_output, run


class LLVMTypeSize:
    # Type sizes in BYTES
    T_CHAR = 1
    T_PTR = 2
    T_INT = 4


class LLVMTypes:
    T_INT = ir.IntType(8 * LLVMTypeSize.T_INT)

    # Memory is byte-addressable so i1 corresponds
    # to 1 byte of space in memory and not 1 bit.
    # The i1 signature is left on purpose to deal
    # with conditional branches.
    T_BOOL = ir.IntType(1)

    T_CHAR = ir.IntType(8 * LLVMTypeSize.T_CHAR)
    T_PROC = ir.VoidType()
    T_PTR = ir.PointerType(8 * LLVMTypeSize.T_PTR)
    T_REAL = ir.DoubleType()
    T_NIL = ir.IntType(8).as_pointer()

    mapping = {
        'integer': T_INT,
        'boolean': T_BOOL,
        'real': T_REAL,
        'char': T_CHAR
    }


class LLVMConstants:
    ZERO_INT = ir.Constant(LLVMTypes.T_INT, 0)
    ZERO_REAL = ir.Constant(LLVMTypes.T_REAL, 0)
    NIL = ir.Constant(LLVMTypes.T_NIL, 0)


class LLVMOperators:

    # Accessible with comp_mapping.get(x, x)
    comp_mapping = {
        '=': '==',
        '<>': '!=',
    }

    @staticmethod
    def get_op(op):
        return LLVMOperators.comp_mapping.get(op, op)


class PCLCodegen:

    def __init__(self):
        ''' Initialize  llvm '''
        self.binding = binding
        self.binding.initialize()
        self.binding.initialize_native_target()
        self.binding.initialize_native_asmprinter()

        # Declare module
        self.module = ir.Module()
        self.module.triple = self.binding.get_default_triple()

        # Declare main function
        func_type = ir.FunctionType(ir.VoidType(), [], False)
        base_func = ir.Function(self.module, func_type, name='main')
        block = base_func.append_basic_block()

        # Declare builder
        self.builder = ir.IRBuilder(block)

    def postprocess_module(self, level=2):
        ''' Module post-processing '''
        self.builder.ret_void()

        # Verify module
        self.module = self.binding.parse_assembly(str(self.module))
        self.module.verify()

        # Optimize module
        self.optimize_module(level=level)

    def optimize_module(self, level=2):
        if level == 0:
            return
        elif level < 0 or level >= 3:
            msg = 'Undefined optimization level: {}'.format(level)
            raise PCLCodegenError(msg)

        # Initialize pass manager builder
        self.pmb = binding.PassManagerBuilder()

        # Declare optimization level
        self.pmb.opt_level = level

        # Run LOCAL optimizations on functions
        self.fpm = binding.FunctionPassManager(self.module)
        self.pmb.populate(self.fpm)
        self.fpm.initialize()

        for fcn in self.module.functions:
            self.fpm.run(fcn)

        self.fpm.finalize()

        # Configure module pass manager
        self.mpm = binding.ModulePassManager()
        self.pmb.populate(self.mpm)

        # Run GLOBAL optimizations on the module
        self.mpm.run(self.module)

    def generate_outputs(self, filename, llc_to_stdout=False):
        llvm_filename = filename + '.imm'
        with open(llvm_filename, 'w+') as f:
            f.write(str(self.module))
        if llc_to_stdout:
            os.system('llc -o - -filetype=obj {}'.format(llvm_filename))
            os.remove(llvm_filename)
        else:
            obj_filename = filename + '.o'
            output_filename = filename + '.out'

            os.system(
                'llc -filetype=obj {} -o {}'.format(llvm_filename, obj_filename))
            os.system(
                'gcc {} -Wall -lbuiltins -lm -o {}'.format(obj_filename, output_filename))
