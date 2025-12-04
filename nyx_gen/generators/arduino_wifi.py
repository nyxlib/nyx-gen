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

lib_deps = PubSubClient, arduino-timer, https://github.com/nyxlib/nyx-node.git

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

#include <Arduino.h>

#ifdef ARDUINO_ARCH_ESP8266
#  include <ESP8266WiFi.h>
#else
#  include <WiFi.h>
#endif

#include "autogen/glue.{{ head_ext }}"
#include "credentials.{{ head_ext }}"

/*--------------------------------------------------------------------------------------------------------------------*/

static nyx_node_t *node = nullptr;

/*--------------------------------------------------------------------------------------------------------------------*/

void setup()
{
    /*----------------------------------------------------------------------------------------------------------------*/

    Serial.begin(115200);

    while(!Serial)
    {
        Serial.print(".");

        delay(50);
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    #ifdef WIFI_STA
    WiFi.mode(WIFI_STA);
    #endif

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while(WiFi.status() != WL_CONNECTED)
    {
        Serial.print(".");

        delay(100);
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    Serial.print('\\n');

    nyx_set_log_level(NYX_LOG_LEVEL_INFO);

    NYX_LOG_INFO("IP: %s", WiFi.localIP().toString().c_str());

    /*----------------------------------------------------------------------------------------------------------------*/

    nyx_memory_initialize();

    /*----------------------------------------------------------------------------------------------------------------*/

    nyx_glue_initialize();

    /*----------------------------------------------------------------------------------------------------------------*/

    static nyx_dict_t *vector_list[] = {
{%- for d in devices -%}
{%-   for v in d.vectors %}
        vector_{{ d.name|lower }}_{{ v.name|lower }},
{%-   endfor -%}
{%- endfor %}
        {{ null }},
    };

    /*----------------------------------------------------------------------------------------------------------------*/

    node = nyx_node_initialize(
        "{{ descr.nodeName }}",
        vector_list,
        {% if descr.enableINDI %}"{{ descr.indiURL }}"{% else %}{{ null }}{% endif %},
        {% if descr.enableMQTT %}"{{ descr.mqttURL }}"{% else %}{{ null }}{% endif %},
        {% if descr.enableNSS %}"{{ descr.nssURL }}"{% else %}{{ null }}{% endif %},
        MQTT_USERNAME,
        MQTT_PASSWORD,
        {{ null }},
        3000,
        true
    );

    /*----------------------------------------------------------------------------------------------------------------*/

    nyx_device_initialize(node);

    /*----------------------------------------------------------------------------------------------------------------*/
}

/*--------------------------------------------------------------------------------------------------------------------*/

void loop()
{
    if(node != nullptr)
    {
        nyx_node_poll(node, {{ descr.nodeTimeout }});
    }
}

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
