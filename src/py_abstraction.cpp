/* SPDX-License-Identifier: MIT */
/* Copyright © 2020 Max Bachmann */

#include "py_common.hpp"
#include "py_fuzz.hpp"
#include "py_string_metric.hpp"
#include "py_process.hpp"
#include "py_utils.hpp"


PyTypeObject PyExtractIter_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    .tp_name = "extract_iter",
    .tp_doc = "",
    .tp_basicsize = sizeof(ExtractIterState),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)extract_iter_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_iter = PyObject_SelfIter,
    .tp_iternext = (iternextfunc)extract_iter_next,
    .tp_alloc = PyType_GenericAlloc,
    .tp_new = extract_iter_new
};


static PyMethodDef methods[] = {
    /* utils */
    PY_METHOD(default_process),
    /* string_metric */
    PY_METHOD(levenshtein),
    PY_METHOD(normalized_levenshtein),
    PY_METHOD(hamming),
    PY_METHOD(normalized_hamming),
    /* fuzz */
    PY_METHOD(ratio),
    PY_METHOD(partial_ratio),
    PY_METHOD(token_sort_ratio),
    PY_METHOD(partial_token_sort_ratio),
    PY_METHOD(token_set_ratio),
    PY_METHOD(partial_token_set_ratio),
    PY_METHOD(token_ratio),
    PY_METHOD(partial_token_ratio),
    PY_METHOD(WRatio),
    PY_METHOD(QRatio),
    /* process */
    PY_METHOD(extractOne),
    /* sentinel */
    {NULL, NULL, 0, NULL}};


#if PY_VERSION_HEX < PYTHON_VERSION(3, 0, 0)

PyMODINIT_FUNC initcpp_impl(void)
{
  if (PyType_Ready(&PyExtractIter_Type) < 0) {
    return;
  }

  PyObject* module = Py_InitModule3(cpp_impl, methods, NULL);

  if (!module) {
    return;
  }

  Py_INCREF((PyObject *)&PyExtractIter_Type);
  PyModule_AddObject(module, "extract_iter", (PyObject *)&PyExtractIter_Type);
}

#else

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "cpp_impl",
    NULL,
    -1,
    methods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyMODINIT_FUNC PyInit_cpp_impl(void)
{
  if (PyType_Ready(&PyExtractIter_Type) < 0) {
    return NULL;
  }

  PyObject* module = PyModule_Create(&moduledef);

  if (!module) {
    return NULL;
  }

  Py_INCREF((PyObject *)&PyExtractIter_Type);
  if (PyModule_AddObject(module, "extract_iter", (PyObject *)&PyExtractIter_Type) < 0) {
    Py_DECREF(module);
    Py_DECREF(PyExtractIter_Type);
    return NULL;
  }

  return module;
}

#endif
