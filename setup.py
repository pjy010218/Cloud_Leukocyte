from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "hierarchical_policy_engine_cython",
        ["hierarchical_policy_engine_cython.pyx"],
        language="c++",
    )
]

setup(
    name="hierarchical_policy_engine_cython",
    ext_modules=cythonize(extensions),
)
