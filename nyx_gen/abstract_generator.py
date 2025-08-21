# -*- coding: utf-8 -*-
########################################################################################################################

import os
import abc
import glob
import shutil
import typing
import inspect
import argparse

from importlib import util

from jinja2 import Environment, StrictUndefined

########################################################################################################################

def generator_config(name: str, null: str, src_ext: str, head_ext: str):

    def decorator(cls: 'AbstractGenerator') -> 'AbstractGenerator':

        cls._name = name
        cls._null = null
        cls._src_ext = src_ext
        cls._head_ext = head_ext

        return cls

    return decorator

########################################################################################################################

class AbstractGenerator(abc.ABC):

    ####################################################################################################################

    _name: str = None
    _null: str = None
    _src_ext: str = None
    _head_ext: str = None

    ####################################################################################################################

    _env = Environment(undefined = StrictUndefined, trim_blocks = False, lstrip_blocks = False, keep_trailing_newline = True, newline_sequence = '\n')

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

    result = {}

    ####################################################################################################################

    for file in sorted(glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'generators', '*.py'))):

        spec = util.spec_from_file_location('nyx_gen.generators.{}'.format(os.path.split(os.path.splitext(file)[0])[1]), file)

        mod = util.module_from_spec(spec)

        spec.loader.exec_module(mod)

        ##

        for _, generator in inspect.getmembers(mod, inspect.isclass):

            try:

                if (
                    generator._name is not None
                    and
                    generator._null is not None
                    and
                    generator._src_ext is not None
                    and
                    generator._head_ext is not None
                    and
                    issubclass(generator, AbstractGenerator)
                ):

                    result[generator._name] = generator

            except Exception as e:

                print('Error importing `{}`: {}'.format(file, e.__str__()))

    ####################################################################################################################

    return result

########################################################################################################################
