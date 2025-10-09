# -*- coding: utf-8 -*-
########################################################################################################################

import os
import re
import abc
import shutil
import typing
import argparse

from jinja2 import Environment, StrictUndefined

########################################################################################################################

NYX_NUMBER_INT    = 0
NYX_NUMBER_UINT   = 1
NYX_NUMBER_LONG   = 2
NYX_NUMBER_ULONG  = 3
NYX_NUMBER_DOUBLE = 4

########################################################################################################################

FORMAT_RE = re.compile(r'%([0-9.*+-]*)?(?P<long>l)?(?P<type>[a-zA-Z])')

########################################################################################################################

def get_number_type(fmt: str) -> int:

    ####################################################################################################################

    m = FORMAT_RE.search(fmt)

    if not m:

        raise ValueError(f'Invalid format: {fmt}')

    ####################################################################################################################

    l = m.group('long') \
                    is not None
    t = m.group('type')

    ####################################################################################################################

    if t in ('d', 'i'):
        return NYX_NUMBER_LONG if l else NYX_NUMBER_INT
    elif t in ('u', 'o', 'x', 'X'):
        return NYX_NUMBER_ULONG if l else NYX_NUMBER_UINT
    elif t in ('f', 'F', 'e', 'E', 'g', 'G', 'a', 'A', 'm'):
        return NYX_NUMBER_DOUBLE
    else:
        raise ValueError(f'Unsupported type specifier: %{t}')

########################################################################################################################

def generator_config(name: str, null: str, src_ext: str, head_ext: str):

    def f(cls: 'AbstractGenerator') -> 'AbstractGenerator':

        cls._name = name
        cls._null = null
        cls._src_ext = src_ext
        cls._head_ext = head_ext

        return cls

    return f

########################################################################################################################

class AbstractGenerator(abc.ABC):

    ####################################################################################################################

    _name: str = None
    _null: str = None
    _src_ext: str = None
    _head_ext: str = None

    ####################################################################################################################

    _env = Environment(undefined = StrictUndefined, trim_blocks = False, lstrip_blocks = False, keep_trailing_newline = True, newline_sequence = '\n', finalize = (lambda v:
        (v.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n').replace('\t', '\\t'))
        if isinstance(v, str) else v
    ))

    ####################################################################################################################

    # noinspection PyUnresolvedReferences
    def __init__(self, args: argparse.Namespace, descr: dict):

        ################################################################################################################

        self._override_project: str = args.override_project
        self._override_device: str = args.override_device
        self._override_main: str = args.override_main
        self._override_cmake: str = args.override_cmake

        self._descr = descr

        ################################################################################################################

        self._devices = sorted((dict(d) for d in descr['devices'].values()), key = lambda x: x['rank'])

        for device in self._devices:

            device['vectors'] = sorted((dict(vectors) for vectors in device['vectors'].values()), key = lambda x: x['rank'])

            for vector in device['vectors']:

                vector['defs'] = sorted((dict(vector_defs) for vector_defs in vector['defs'].values()), key = lambda x: x['rank'])

        ################################################################################################################

        self._driver_path: str = os.path.join(args.output, descr['nodeName']).__str__()

        if self._override_project and os.path.isdir(self._driver_path):

            shutil.rmtree(self._driver_path)

    ####################################################################################################################

    def create_directories(self) -> None:

        os.makedirs(os.path.join(self._driver_path, 'include'), exist_ok = True)

        os.makedirs(os.path.join(self._driver_path, 'src', 'autogen'), exist_ok = True)

    ####################################################################################################################

    def render(self, template: str, /, **context: typing.Any) -> str:

        context = dict(context)

        context['descr'] = self._descr

        context['null'] = self.__class__._null
        context['src_ext'] = self.__class__._src_ext
        context['head_ext'] = self.__class__._head_ext

        return AbstractGenerator._env.from_string(template).render(**context)

    ####################################################################################################################

    @abc.abstractmethod
    def generate(self) -> None:

        pass

########################################################################################################################

# noinspection PyProtectedMember
def detect_generators() -> typing.Dict[str, typing.Type[AbstractGenerator]]:

    ####################################################################################################################

    from .generators.posix_c import PosixCGenerator
    from .generators.posix_cpp import PosixCPPGenerator
    from .generators.gnuradio import GNURadioGenerator
    from .generators.arduino_eth import ArduinoEthGenerator
    from .generators.arduino_wifi import ArduinoWifiGenerator

    ####################################################################################################################

    result = {
        PosixCGenerator._name: PosixCGenerator,
        PosixCPPGenerator._name: PosixCPPGenerator,
        GNURadioGenerator._name: GNURadioGenerator,
        ArduinoEthGenerator._name: ArduinoEthGenerator,
        ArduinoWifiGenerator._name: ArduinoWifiGenerator,
    }

    ####################################################################################################################

    return result

########################################################################################################################

AbstractGenerator._env.filters['pascalcase'] = lambda s: ''.join(part.capitalize() for part in s.split('_') if part)

AbstractGenerator._env.globals['NYX_NUMBER_INT'] = NYX_NUMBER_INT
AbstractGenerator._env.globals['NYX_NUMBER_UINT'] = NYX_NUMBER_UINT
AbstractGenerator._env.globals['NYX_NUMBER_LONG'] = NYX_NUMBER_LONG
AbstractGenerator._env.globals['NYX_NUMBER_ULONG'] = NYX_NUMBER_ULONG
AbstractGenerator._env.globals['NYX_NUMBER_DOUBLE'] = NYX_NUMBER_DOUBLE

AbstractGenerator._env.globals['get_number_type'] = get_number_type

########################################################################################################################
