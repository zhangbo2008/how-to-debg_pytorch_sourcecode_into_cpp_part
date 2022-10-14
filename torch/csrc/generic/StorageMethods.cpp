static PyObject * THPStorage_(size)(THPStorage *self)
{
  HANDLE_TH_ERRORS
  return PyLong_FromLong(THStorage_(size)(LIBRARY_STATE self->cdata));
  END_HANDLE_TH_ERRORS
}

static PyObject * THPStorage_(elementSize)(THPStorage *self)
{
  HANDLE_TH_ERRORS
  return PyLong_FromLong(THStorage_(elementSize)(LIBRARY_STATE_NOARGS));
  END_HANDLE_TH_ERRORS
}

static PyObject * THPStorage_(retain)(THPStorage *self)
{
  HANDLE_TH_ERRORS
  THStorage_(retain)(LIBRARY_STATE self->cdata);
  return (PyObject*)self;
  END_HANDLE_TH_ERRORS
}

static PyObject * THPStorage_(free)(THPStorage *self)
{
  HANDLE_TH_ERRORS
  THStorage_(free)(LIBRARY_STATE self->cdata);
  return (PyObject*)self;
  END_HANDLE_TH_ERRORS
}

static PyObject * THPStorage_(new)(THPStorage *self)
{
  HANDLE_TH_ERRORS
  THStoragePtr new_storage = THStorage_(new)(LIBRARY_STATE_NOARGS);
  PyObject *_ret = THPStorage_(newObject)(new_storage);
  new_storage.release();
  return _ret;
  END_HANDLE_TH_ERRORS
}

static PyObject * THPStorage_(resize_)(THPStorage *self, PyObject *number_arg)
{
  HANDLE_TH_ERRORS
  long newsize;
  if (!THPUtils_getLong(number_arg, &newsize))
    return NULL;
  THStorage_(resize)(LIBRARY_STATE self->cdata, newsize);
  Py_INCREF(self);
  return (PyObject*)self;
  END_HANDLE_TH_ERRORS
}

static PyObject * THPStorage_(fill_)(THPStorage *self, PyObject *number_arg)
{
  HANDLE_TH_ERRORS
  real rvalue;
  if (!THPUtils_(parseReal)(number_arg, &rvalue))
    return NULL;
  THStorage_(fill)(LIBRARY_STATE self->cdata, rvalue);
  Py_INCREF(self);
  return (PyObject*)self;
  END_HANDLE_TH_ERRORS
}

PyObject * THPStorage_(writeFile)(THPStorage *self, PyObject *file)
{
  HANDLE_TH_ERRORS
  int fd = PyObject_AsFileDescriptor(file);
  if (fd == -1) {
    THPUtils_setError("_write_file couln't retrieve file descriptor from given object");
    return NULL;
  }
  THPStorage_(writeFileRaw)(self->cdata, fd);
  Py_RETURN_NONE;
  END_HANDLE_TH_ERRORS
}

PyObject * THPStorage_(newWithFile)(PyObject *_unused, PyObject *file)
{
  HANDLE_TH_ERRORS
  int fd = PyObject_AsFileDescriptor(file);
  if (fd == -1) {
    THPUtils_setError("_new_with_file couln't retrieve file descriptor from given object");
    return NULL;
  }
  THStoragePtr storage = THPStorage_(readFileRaw)(fd);
  PyObject *result = THPStorage_(newObject)(storage);
  storage.release();
  return result;
  END_HANDLE_TH_ERRORS
}

static PyMethodDef THPStorage_(methods)[] = {
  {"elementSize", (PyCFunction)THPStorage_(elementSize), METH_NOARGS, NULL},
  {"fill_", (PyCFunction)THPStorage_(fill_), METH_O, NULL},
  {"free", (PyCFunction)THPStorage_(free), METH_NOARGS, NULL},
  {"new", (PyCFunction)THPStorage_(new), METH_NOARGS, NULL},
  {"resize_", (PyCFunction)THPStorage_(resize_), METH_O, NULL},
  {"retain", (PyCFunction)THPStorage_(retain), METH_NOARGS, NULL},
  {"size", (PyCFunction)THPStorage_(size), METH_NOARGS, NULL},
  {"_write_file", (PyCFunction)THPStorage_(writeFile), METH_O, NULL},
  {"_new_with_file", (PyCFunction)THPStorage_(newWithFile), METH_O | METH_STATIC, NULL},
  {NULL}
};
