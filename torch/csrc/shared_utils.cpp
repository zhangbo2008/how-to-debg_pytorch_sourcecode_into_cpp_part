bool THPUtils_checkLong(PyObject *index) {
    return PyLong_Check(index) || PyInt_Check(index);
}

int THPUtils_getLong(PyObject *index, long *result) {
  if (PyLong_Check(index)) {
    *result = PyLong_AsLong(index);
  } else if (PyInt_Check(index)) {
    *result = PyInt_AsLong(index);
  } else {
    char err_string[512];
    snprintf (err_string, 512, "%s %s",
      "getLong expected int or long, but got type: ",
      index->ob_type->tp_name);
    PyErr_SetString(PyExc_RuntimeError, err_string);
    return 0;
  }
  return 1;
}

int THPUtils_getCallable(PyObject *arg, PyObject **result) {
  if (!PyCallable_Check(arg))
    return 0;
  *result = arg;
  return 1;
}

THLongStorage * THPUtils_getLongStorage(PyObject *args, int ignore_first) {
  long value;

  Py_ssize_t length = PyTuple_Size(args);
  if (length < ignore_first+1)
      return NULL;

  // Maybe there's a LongStorage
  PyObject *first_arg = PyTuple_GET_ITEM(args, ignore_first);
  if (length == ignore_first+1 && THPLongStorage_IsSubclass(first_arg)) {
    THPLongStorage *storage = (THPLongStorage*)first_arg;
    THLongStorage_retain(storage->cdata);
    return storage->cdata;
  }

  // If not, let's try to parse the numbers
  THLongStoragePtr result = THLongStorage_newWithSize(length-ignore_first);
  for (Py_ssize_t i = ignore_first; i < length; ++i) {
    PyObject *arg = PyTuple_GET_ITEM(args, i);
    if (!THPUtils_getLong(arg, &value))
        return NULL;
    result->data[i-ignore_first] = value;
  }
  return result.release();
}

void THPUtils_setError(const char *format, ...)
{
  static const size_t ERROR_BUFFER_SIZE = 1000;
  char buffer[ERROR_BUFFER_SIZE];
  va_list fmt_args;

  va_start(fmt_args, format);
  vsnprintf(buffer, ERROR_BUFFER_SIZE, format, fmt_args);
  va_end(fmt_args);
  PyErr_SetString(PyExc_RuntimeError, buffer);
}


void THPUtils_invalidArguments(PyObject *given_args, const char *expected_args_desc) {
  static const size_t BUFFER_SIZE = 10000;
  static const std::string PREFIX = "Invalid arguments! Got ";
  std::string error_msg;
  error_msg.reserve(2000);
  error_msg += PREFIX;

  // TODO: assert that args is a tuple?
  Py_ssize_t num_args = PyTuple_Size(given_args);
  if (num_args == 0) {
    error_msg += "no arguments";
  } else {
    error_msg += "(";
    for (int i = 0; i < num_args; i++) {
      PyObject *arg = PyTuple_GET_ITEM(given_args, i);
      if (i > 0)
        error_msg += ", ";
      error_msg += Py_TYPE(arg)->tp_name;
    }
    error_msg += ")";
  }
  error_msg += ", but expected ";
  error_msg += expected_args_desc;
  PyErr_SetString(PyExc_ValueError, error_msg.c_str());
}

template<>
void THPPointer<THPGenerator>::free() {
  if (ptr)
    Py_DECREF(ptr);
}

template<>
void THPPointer<PyObject>::free() {
  if (ptr)
    Py_DECREF(ptr);
}

template class THPPointer<THPGenerator>;
template class THPPointer<PyObject>;
