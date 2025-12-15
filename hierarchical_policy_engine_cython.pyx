# cython: language_level=3
# distutils: language = c++

from libcpp.string cimport string
from libcpp.vector cimport vector

cdef extern from "node.h":
    cdef cppclass PolicyEngine:
        PolicyEngine() except +
        void allow_path(const char* path)
        void suppress_path(const char* path)
        string check_access(const char* path)
        vector[string] intersection(PolicyEngine* other)
        vector[string] flatten()

cdef class HierarchicalPolicyEngine:
    cdef PolicyEngine* engine

    def __cinit__(self):
        self.engine = new PolicyEngine()

    def __dealloc__(self):
        del self.engine

    cpdef void allow_path(self, str path):
        cdef bytes py_bytes = path.encode('utf-8')
        self.engine.allow_path(py_bytes)

    cpdef void suppress_path(self, str path):
        cdef bytes py_bytes = path.encode('utf-8')
        self.engine.suppress_path(py_bytes)

    cpdef str check_access(self, str path):
        cdef bytes py_bytes = path.encode('utf-8')
        cdef string result = self.engine.check_access(py_bytes)
        return result.decode('utf-8')

    cpdef list intersection(self, HierarchicalPolicyEngine other):
        cdef vector[string] result = self.engine.intersection(other.engine)
        return [s.decode('utf-8') for s in result]

    cpdef list flatten(self):
        cdef vector[string] result = self.engine.flatten()
        return [s.decode('utf-8') for s in result]
