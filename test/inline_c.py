#! /usr/bin/env python
# ______________________________________________________________________
'''inline_c.py

Demonstrates using llvm-py and clang to inline C extension code.
'''
# ______________________________________________________________________

import distutils
import StringIO
import subprocess
import sys
import llvm.core
import llvm.ee

# ______________________________________________________________________

TEST_SRC = '''#include <Python.h>

static PyObject *
demoext_demofn(PyObject * self, PyObject * args)
{
  if (!PyArg_ParseTuple(args, "")) return NULL;
  printf("Inside dynamically compiled C module!\\n");
  return PyLong_FromLong(42);
}

static PyMethodDef demo_methods[] = {
    {"demofn",  demoext_demofn, METH_VARARGS, "Be really lazy."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initdemoext(void)
{
  PyObject * module_obj = (PyObject *)NULL;
  if (!(module_obj = Py_InitModule("demoext", demo_methods))) return;
}
'''

# ______________________________________________________________________

class CLangError (Exception):
    pass

# ______________________________________________________________________

def c2ll (c_source, *args):
    cmd_list = ['clang', '-I', distutils.sysconfig_get_python_inc(), '-S',
                '-emit-llvm', '-o', '-', '-x', 'c']
    cmd_list += list(args)
    cmd_list.append('-')
    clang_proc = subprocess.Popen(cmd_list,
                                  stdin = subprocess.PIPE,
                                  stdout = subprocess.PIPE,
                                  stderr = subprocess.PIPE)
    ret_val, errs = clang_proc.communicate(c_source)
    if not ret_val:
        raise CLangError(errs)
    return ret_val

# ______________________________________________________________________

def llvm_module_from_c_source (c_source, *args):
    return llvm.core.Module.from_assembly(StringIO.StringIO(c2ll(c_source,
                                                                 *args)))

# ______________________________________________________________________

__dyngen_modules__ = {}

def py_module_from_c_source (module_name, c_source, *args):
    global __dyngen_modules__
    c_source_hash = hash(c_source)
    if c_source_hash in __dyngen_modules__:
        ret_val = __dyngen_modules__[-1]
    else:
        llvm_module = llvm_module_from_c_source(c_source, *args)
        init_fn = llvm_module.get_function_named('init' + module_name)
        ee = llvm.ee.ExecutionEngine.new(llvm_module)
        ee.run_function(init_fn, [])
        ret_val = sys.modules[module_name]
        __dyngen_modules__[c_source_hash] = (llvm_module, ee, ret_val)
    return ret_val

# ______________________________________________________________________

def main (*args, **kws):
    m = llvm_module_from_c_source(TEST_SRC)
    print m
    ee = llvm.ee.ExecutionEngine.new(m)
    init_fn = m.get_function_named('initdemoext')
    ee.run_function(init_fn, [])
    demoext = sys.modules['demoext']
    assert demoext.demofn() == 42L

# ______________________________________________________________________

if __name__ == "__main__":
    main(*sys.argv[1:])

# ______________________________________________________________________
# End of inline_c.py
