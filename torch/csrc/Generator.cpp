#include <Python.h>
#include <structmember.h>

#include <stdbool.h>
#include <TH/TH.h>
#include "THP.h"

extern PyObject *THPGeneratorClass;

static void THPGenerator_dealloc(THPGenerator* self)
{
  THGenerator_free(self->cdata);
  Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject * THPGenerator_pynew(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
  HANDLE_TH_ERRORS
  if ((args && PyTuple_Size(args) != 0) || kwargs) {
    THPUtils_setError("torch.Generator doesn't constructor doesn't accept any arguments");
    return NULL;
  }
  THPGeneratorPtr self = (THPGenerator *)type->tp_alloc(type, 0);
  self->cdata = THGenerator_new();

  return (PyObject*)self.release();
  END_HANDLE_TH_ERRORS
}

PyTypeObject THPGeneratorType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  "torch.C.Generator",                   /* tp_name */
  sizeof(THPGenerator),                   /* tp_basicsize */
  0,                                     /* tp_itemsize */
  (destructor)THPGenerator_dealloc,     /* tp_dealloc */
  0,                                     /* tp_print */
  0,                                     /* tp_getattr */
  0,                                     /* tp_setattr */
  0,                                     /* tp_reserved */
  0,                                     /* tp_repr */
  0,                                     /* tp_as_number */
  0,                                     /* tp_as_sequence */
  0,                                     /* tp_as_mapping */
  0,                                     /* tp_hash  */
  0,                                     /* tp_call */
  0,                                     /* tp_str */
  0,                                     /* tp_getattro */
  0,                                     /* tp_setattro */
  0,                                     /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
  NULL,                                  /* tp_doc */
  0,                                     /* tp_traverse */
  0,                                     /* tp_clear */
  0,                                     /* tp_richcompare */
  0,                                     /* tp_weaklistoffset */
  0,                                     /* tp_iter */
  0,                                     /* tp_iternext */
  0,   /* will be assigned in init */    /* tp_methods */
  0,   /* will be assigned in init */    /* tp_members */
  0,                                     /* tp_getset */
  0,                                     /* tp_base */
  0,                                     /* tp_dict */
  0,                                     /* tp_descr_get */
  0,                                     /* tp_descr_set */
  0,                                     /* tp_dictoffset */
  0,                                     /* tp_init */
  0,                                     /* tp_alloc */
  THPGenerator_pynew,                    /* tp_new */
};

bool THPGenerator_Check(PyObject *obj)
{
  return Py_TYPE(obj) == &THPGeneratorType;
}

PyObject * THPGenerator_newObject()
{
  // TODO: error checking
  THPObjectPtr args = PyTuple_New(0);
  return PyObject_Call((PyObject*)&THPGeneratorType, args, NULL);
}

//static struct PyMemberDef THPStorage_(members)[] = {
  //{(char*)"_cdata", T_ULONGLONG, offsetof(THPGenerator, cdata), READONLY, NULL},
  //{NULL}
//};

bool THPGenerator_init(PyObject *module)
{
  THPGeneratorClass = (PyObject*)&THPGeneratorType;
  //THPStorageType.tp_methods = THPStorage_(methods);
  //THPStorageType.tp_members = THPStorage_(members);
  if (PyType_Ready(&THPGeneratorType) < 0)
    return false;
  Py_INCREF(&THPGeneratorType);
  PyModule_AddObject(module, "Generator", (PyObject *)&THPGeneratorType);
  return true;
}
