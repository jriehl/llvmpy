#! /usr/bin/env python
# ______________________________________________________________________
'''The goal of this test is to build and demonstrate the following
LLVM assembly code using the API:

@msg = internal constant [15 x i8] c"Hello, world.\\0A\\00"
declare i32 @puts(i8 *)
define i32 @not_really_main() {
    %cst = getelementptr [15 x i8]* @msg, i32 0, i32 0
    call i32 @puts(i8 * %cst)
    ret i32 0
}
'''

import llvm.core as lc
import llvm.ee as le

# ______________________________________________________________________

def main (*args, **kws):
    m = lc.Module.new(b'demo_module')
    i8 = lc.Type.int(8)
    i32 = lc.Type.int(32)
    i8ptr = lc.Type.pointer(i8)
    puts_ty = lc.Type.function(i32, [i8ptr])
    puts_decl = m.add_function(puts_ty, b'puts')
    hello_fn_ty = lc.Type.function(i32, [])
    hello_fn = m.add_function(hello_fn_ty, b'hello_fn')
    bb = hello_fn.append_basic_block(b'entry')
    builder = lc.Builder.new(bb)

    # Was having a devil of time using stringz(), since it returns a
    # value of type [15 x i8], as opposed to [15 x i8]*.  The weird
    # part is that global variables seem to become pointer types when
    # used inside functions.

    # See: http://comments.gmane.org/gmane.comp.compilers.llvm.devel/28601

    hello_str = lc.Constant.stringz(b'Hello, world.\n')
    hello_var = m.add_global_variable(hello_str.type, b'msg')
    # Required a patch to get this to work.
    # XXX Need to extend patch to other constant constructors in core.py.
    hello_var._set_initializer(hello_str)

    zero = lc.Constant.int(i32, 0)
    cst = builder.gep(hello_var, [zero, zero], b'cst')
    builder.call(puts_decl, [cst])
    builder.ret(zero)
    print(str(m.__str__()))
    ee = le.ExecutionEngine.new(m)
    ee.run_function(hello_fn, [])

# ______________________________________________________________________

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])

# ______________________________________________________________________
# End of test_puts_demo.py
