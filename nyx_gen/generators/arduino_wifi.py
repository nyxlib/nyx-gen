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

    ####################################################################################################################

    def _generate_main(self) -> None:

        ################################################################################################################
        # credentials.h                                                                                                #
        ################################################################################################################

        template = '''
#define WIFI_SSID {% if descr.wifiSSID %}"{{ descr.wifiSSID }}"{% else %}{{ null }}{% endif %}
#define WIFI_PASSWORD {% if descr.wifiPassword %}"{{ descr.wifiPassword }}"{% else %}{{ null }}{% endif %}
#define MQTT_USERNAME {% if descr.enableMQTT %}"{{ descr.mqttUsername }}"{% else %}{{ null }}{% endif %}
#define MQTT_PASSWORD {% if descr.enableMQTT %}"{{ descr.mqttPassword }}"{% else %}{{ null }}{% endif %}
#define REDIS_USERNAME {% if descr.enableRedis %}"{{ descr.redisUsername }}"{% else %}{{ null }}{% endif %}
#define REDIS_PASSWORD {% if descr.enableRedis %}"{{ descr.redisPassword }}"{% else %}{{ null }}{% endif %}
'''[1:]

        filename = os.path.join(self._driver_path, 'src', f'credentials.{self._head_ext}')

        with open(filename, 'wt', encoding = 'utf-8') as f:

            f.write(self.render(
                template
            ))

        ################################################################################################################
        # main.c                                                                                                       #
        ################################################################################################################

        template = '''

/*--------------------------------------------------------------------------------------------------------------------*/
'''[1:]

        filename = os.path.join(self._driver_path, 'src', f'main.{self._src_ext}')

        if self._override_main or not os.path.isfile(filename):

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self.render(
                    template,
                    devices = self._devices
                ))

########################################################################################################################
