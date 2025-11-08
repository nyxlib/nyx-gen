# -*- coding: utf-8 -*-
########################################################################################################################

import os

########################################################################################################################

from .posix_c import PosixCGenerator

from ..abstract_generator import generator_config

########################################################################################################################

@generator_config(name = 'arduino-wifi', null = 'nullptr', src_ext = 'cpp', head_ext = 'hpp')
class ArduinoWifiGenerator(PosixCGenerator):

    ####################################################################################################################

    def _generate_cmake(self) -> None:

        platform, board, ram = self._descr['board'].split('|')

        template = f'''
; PlatformIO Project Configuration File
;
;   Build options: build flags, source filter
;   Upload options: custom upload port, speed and extra flags
;   Library options: dependencies, extra library storages
;   Advanced options: extra scripting
;
; Please visit documentation for the other options and examples
; https://docs.platformio.org/page/projectconf.html

[env]
build_flags = -DNYX_HAS_WIFI -DNYX_RAM_SIZE={ram} -Wno-unused-function

lib_deps = PubSubClient, https://github.com/nyxlib/nyx-node.git

lib_ignore = FATFilesystem

monitor_speed = 115200

[env:nyx_node]
platform = {platform}
board = {board}
framework = arduino
'''[1:]

        filename = os.path.join(self._driver_path, 'platformio.ini')

        if self._override_cmake or not os.path.isfile(filename):

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self.render(
                    template,
                    platform = platform,
                    board = board,
                    ram = ram
                ))

########################################################################################################################
