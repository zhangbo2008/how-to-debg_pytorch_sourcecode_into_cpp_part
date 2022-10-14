#include <Python.h>

#include <stdbool.h>
#include <unordered_map>
#include <TH/TH.h>

#include "THCP.h"

THCState _state;
THCState *state = &_state;

////////////////////////////////////////////////////////////////////////////////
// Class pointer cache
////////////////////////////////////////////////////////////////////////////////

PyObject *THCPDoubleStorageClass = NULL;
PyObject *THCPFloatStorageClass  = NULL;
PyObject *THCPLongStorageClass   = NULL;
PyObject *THCPIntStorageClass    = NULL;
PyObject *THCPHalfStorageClass   = NULL;
PyObject *THCPShortStorageClass  = NULL;
PyObject *THCPCharStorageClass   = NULL;
PyObject *THCPByteStorageClass   = NULL;

PyObject *THCPDoubleTensorClass  = NULL;
PyObject *THCPFloatTensorClass   = NULL;
PyObject *THCPLongTensorClass    = NULL;
PyObject *THCPIntTensorClass     = NULL;
PyObject *THCPHalfTensorClass    = NULL;
PyObject *THCPShortTensorClass   = NULL;
PyObject *THCPCharTensorClass    = NULL;
PyObject *THCPByteTensorClass    = NULL;


static bool THCPModule_loadClasses(PyObject *module_dict)
{
#define ASSERT_NOT_NULL(ptr) if (!(ptr)) { THPUtils_setError("couldn't load classes"); return false; }
  ASSERT_NOT_NULL(THCPDoubleStorageClass = PyMapping_GetItemString(module_dict, (char*)"DoubleStorage"));
  ASSERT_NOT_NULL(THCPFloatStorageClass  = PyMapping_GetItemString(module_dict, (char*)"FloatStorage"));
  ASSERT_NOT_NULL(THCPHalfStorageClass   = PyMapping_GetItemString(module_dict, (char*)"HalfStorage"));
  ASSERT_NOT_NULL(THCPLongStorageClass   = PyMapping_GetItemString(module_dict, (char*)"LongStorage"));
  ASSERT_NOT_NULL(THCPIntStorageClass    = PyMapping_GetItemString(module_dict, (char*)"IntStorage"));
  ASSERT_NOT_NULL(THCPShortStorageClass  = PyMapping_GetItemString(module_dict, (char*)"ShortStorage"));
  ASSERT_NOT_NULL(THCPCharStorageClass   = PyMapping_GetItemString(module_dict, (char*)"CharStorage"));
  ASSERT_NOT_NULL(THCPByteStorageClass   = PyMapping_GetItemString(module_dict, (char*)"ByteStorage"));

  ASSERT_NOT_NULL(THCPDoubleTensorClass  = PyMapping_GetItemString(module_dict, (char*)"DoubleTensor"));
  ASSERT_NOT_NULL(THCPHalfTensorClass    = PyMapping_GetItemString(module_dict, (char*)"HalfTensor"));
  ASSERT_NOT_NULL(THCPFloatTensorClass   = PyMapping_GetItemString(module_dict, (char*)"FloatTensor"));
  ASSERT_NOT_NULL(THCPLongTensorClass    = PyMapping_GetItemString(module_dict, (char*)"LongTensor"));
  ASSERT_NOT_NULL(THCPIntTensorClass     = PyMapping_GetItemString(module_dict, (char*)"IntTensor"));
  ASSERT_NOT_NULL(THCPShortTensorClass   = PyMapping_GetItemString(module_dict, (char*)"ShortTensor"));
  ASSERT_NOT_NULL(THCPCharTensorClass    = PyMapping_GetItemString(module_dict, (char*)"CharTensor"));
  ASSERT_NOT_NULL(THCPByteTensorClass    = PyMapping_GetItemString(module_dict, (char*)"ByteTensor"));

  return true;
#undef ASSERT_NOT_NULL
}

////////////////////////////////////////////////////////////////////////////////
// Tensor stateless methods
////////////////////////////////////////////////////////////////////////////////

static bool THCPModule_assignStateless()
{
#define INIT_STATELESS(type) INIT_STATELESS_DETAIL(type, TH_CONCAT_2(Cuda, type))
#define INIT_STATELESS_DETAIL(type,ctype)                                      \
  stateless = PyObject_Call((PyObject*)&TH_CONCAT_2(ctype, TensorStatelessType), arg, NULL); \
  if (!stateless) {                                                            \
    THPUtils_setError("stateless method initialization error");                \
    return false;                                                              \
  }                                                                            \
  if (PyObject_SetAttrString(TH_CONCAT_3(THCP,type,TensorClass), STATELESS_ATTRIBUTE_NAME, stateless) == -1) { \
    THPUtils_setError("stateless method initialization error (on assignment)");\
  }
  PyObject *arg = PyTuple_New(0);
  PyObject *stateless;
  INIT_STATELESS(Double);
  INIT_STATELESS_DETAIL(Float, Cuda);
  INIT_STATELESS(Long);
  INIT_STATELESS(Int);
  INIT_STATELESS(Short);
  INIT_STATELESS(Char);
  INIT_STATELESS(Byte);
  Py_DECREF(arg);
  return true;
#undef INIT_STATELESS_DETAIL
#undef INIT_STATELESS
}

////////////////////////////////////////////////////////////////////////////////
// Additional copy handlers
////////////////////////////////////////////////////////////////////////////////

#include "ModuleCopy.cpp"

////////////////////////////////////////////////////////////////////////////////
// CUDA management methods
////////////////////////////////////////////////////////////////////////////////

void THCPModule_setDevice(int device)
{
  THCudaCheck(cudaSetDevice(device));
  THCRandom_setGenerator(state, device);

  // The stream is per device, so update the stream as well
  THCState_setStream(state, device, THCState_getCurrentStreamIndex(state));
  THCState_setBlasHandle(state, device, THCState_getCurrentBlasHandleIndex(state));
}

PyObject * THCPModule_setDevice_wrap(PyObject *self, PyObject *arg)
{
  HANDLE_TH_ERRORS
  long device;
  if (!THPUtils_getLong(arg, &device))
    return NULL;

  THCPModule_setDevice(device);

  Py_RETURN_NONE;
  END_HANDLE_TH_ERRORS
}

PyObject * THCPModule_getDevice_wrap(PyObject *self)
{
  HANDLE_TH_ERRORS
  int device;
  THCudaCheck(cudaGetDevice(&device));
  return PyLong_FromLong(device);
  END_HANDLE_TH_ERRORS
}

PyObject * THCPModule_getDeviceCount_wrap(PyObject *self)
{
  HANDLE_TH_ERRORS
  int ndevice;
  THCudaCheck(cudaGetDeviceCount(&ndevice));
  return PyLong_FromLong(ndevice);
  END_HANDLE_TH_ERRORS
}

////////////////////////////////////////////////////////////////////////////////
// Cuda module initialization
////////////////////////////////////////////////////////////////////////////////

bool THCPModule_initCuda(PyObject *module_dict) {
#define ASSERT_TRUE(cond) if (!(cond)) { return false; }
  THCudaInit(state);

#ifdef USE_MAGMA
  THCMagma_init(state);
  ASSERT_TRUE(PyDict_SetItemString(module_dict, "hasMagma", PyBool_FromLong(true)) != -1);
#else
  ASSERT_TRUE(PyDict_SetItemString(module_dict, "hasMagma", PyBool_FromLong(false)) != -1);
#endif

#ifdef CUDA_HALF_TENSOR
  ASSERT_TRUE(PyDict_SetItemString(module_dict, "hasHalf", PyBool_FromLong(true)) != -1);
#else
  ASSERT_TRUE(PyDict_SetItemString(module_dict, "hasHalf", PyBool_FromLong(false)) != -1);
#endif

  ASSERT_TRUE(THCPModule_loadClasses(module_dict));
  ASSERT_TRUE(THCPModule_assignStateless());
  ASSERT_TRUE(THCPModule_initCopy());

  ASSERT_TRUE(PyDict_SetItemString(module_dict, "_state_cdata", PyLong_FromVoidPtr(state)) != -1);

  // TODO: register THCudaShutdown handler at exit
  return true;
#undef ASSERT_TRUE
}

// Callback for python part. Used for additional initialization of python classes
PyObject * THCPModule_initExtension(PyObject *self)
{
  PyObject *torch_module = PyImport_ImportModule("torch.cuda");
  if (!torch_module) {
    THPUtils_setError("class loader couldn't access torch module");
    return NULL;
  }
  PyObject* module_dict = PyModule_GetDict(torch_module);
  return PyBool_FromLong(THCPModule_initCuda(module_dict));
}

