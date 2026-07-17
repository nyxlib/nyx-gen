# -*- coding: utf-8 -*-
########################################################################################################################

import os
import typing

########################################################################################################################

from ..abstract_generator import (
    NYX_NUMBER_DOUBLE,
    NYX_NUMBER_INT,
    NYX_NUMBER_LONG,
    NYX_NUMBER_ULONG,
    NYX_NUMBER_UINT,
    AbstractGenerator,
    generator_config,
    get_number_type,
)

########################################################################################################################

@generator_config(name = 'python', null = 'None', src_ext = 'py', head_ext = 'py')
class PythonGenerator(AbstractGenerator):

    ####################################################################################################################

    def __init__(self, args, descr):

        super().__init__(args, descr)

    ####################################################################################################################

    def create_directories(self) -> None:

        os.makedirs(os.path.join(self._driver_path, 'autogen'), exist_ok = True)

    ####################################################################################################################

    def generate(self) -> None:

        self._generate_package()
        self._generate_glues()
        self._generate_devices()
        self._generate_credentials()
        self._generate_init()
        self._generate_main()

    ####################################################################################################################

    @staticmethod
    def _enum(value: typing.Any, enum: str, prefix: str) -> str:

        if value is None:

            return 'None'

        value = str(value)

        if value.startswith('nyx.'):

            return value

        if value.startswith(f'{enum}.'):

            return f'nyx.{value}'

        if value.startswith(prefix):

            value = value[len(prefix):]

        return f'nyx.{enum}.{value}'

    ####################################################################################################################

    @staticmethod
    def _literal(value: typing.Any) -> str:

        return repr(None if value == 'NULL' else value)

    ####################################################################################################################

    @staticmethod
    def _string(value: typing.Any) -> str:

        return repr('' if value is None else str(value))

    ####################################################################################################################

    @staticmethod
    def _number_prop_class(fmt: str) -> str:

        number_type = get_number_type(fmt)

        if number_type == NYX_NUMBER_INT:

            return 'NyxNumberIntProp'

        if number_type == NYX_NUMBER_UINT:

            return 'NyxNumberUIntProp'

        if number_type == NYX_NUMBER_LONG:

            return 'NyxNumberLongProp'

        if number_type == NYX_NUMBER_ULONG:

            return 'NyxNumberULongProp'

        if number_type == NYX_NUMBER_DOUBLE:

            return 'NyxNumberDoubleProp'

        raise ValueError(f'Unsupported number type: {fmt}')

    ####################################################################################################################

    @staticmethod
    def _prop_class(vector_type: str, number_format: str = None) -> str:

        if vector_type == 'number':

            return PythonGenerator._number_prop_class(number_format)

        if vector_type == 'text':

            return 'NyxTextProp'

        if vector_type == 'light':

            return 'NyxLightProp'

        if vector_type == 'switch':

            return 'NyxSwitchProp'

        if vector_type == 'blob':

            return 'NyxBlobProp'

        if vector_type == 'stream':

            return 'NyxStreamProp'

        raise ValueError(f'Unsupported vector type: {vector_type}')

    ####################################################################################################################

    @staticmethod
    def _vector_class(vector_type: str) -> str:

        if vector_type == 'number':

            return 'NyxNumberVector'

        if vector_type == 'text':

            return 'NyxTextVector'

        if vector_type == 'light':

            return 'NyxLightVector'

        if vector_type == 'switch':

            return 'NyxSwitchVector'

        if vector_type == 'blob':

            return 'NyxBlobVector'

        if vector_type == 'stream':

            return 'NyxStreamVector'

        raise ValueError(f'Unsupported vector type: {vector_type}')

    ####################################################################################################################

    def _render(self, template: str, /, **context: typing.Any) -> str:

        return self.render(
            template,
            enum = self._enum,
            literal = self._literal,
            prop_class = self._prop_class,
            string = self._string,
            vector_class = self._vector_class,
            **context,
        )

    ####################################################################################################################

    def _generate_package(self) -> None:

        template = '''
# -*- coding: utf-8 -*-
########################################################################################################################
# !!! AUTOGENERATED FILE !!!                                                                                           #
########################################################################################################################
'''[1:]

        filename = os.path.join(self._driver_path, 'autogen', '__init__.py')

        with open(filename, 'wt', encoding = 'utf-8') as f:

            f.write(self._render(
                template
            ))

    ####################################################################################################################

    def _generate_glues(self) -> None:

        template = '''
# -*- coding: utf-8 -*-
########################################################################################################################
# !!! AUTOGENERATED FILE !!!
########################################################################################################################

import nyx

########################################################################################################################

class Device{{ device.name|pascalcase }}Glue:

    ####################################################################################################################

    def __init__(self, node: nyx.NyxNode):

        self._node = node

        ################################################################################################################
        # INITIALIZE VECTORS                                                                                           #
        ################################################################################################################
{%- for v in device.vectors %}

        ################################################################################################################
        # {{ '%-108s'|format('VECTOR ' ~ device.name|upper ~ '::' ~ v.name|upper) }}#
        ################################################################################################################
{%- for df in v.defs %}

        self.vector_{{ v.name|lower }}_{{ df.name|lower }} = nyx.{{ prop_class(v.type, df.format|default(None)) }}(
            {{ string(df.name) }},
            {{ string(df.label|default('')) }},{% if v.type == 'number' %}
            {{ string(df.format) }},
            {{ df.min }},
            {{ df.max }},
            {{ df.step }},
            {{ df.value }},{% elif v.type == 'text' %}
            {{ string(df.value|default('')) }},{% elif v.type == 'light' %}
            {{ enum(df.value, 'NyxState', 'NYX_STATE_') }},{% elif v.type == 'switch' %}
            {{ enum(df.value, 'NyxOnOff', 'NYX_ONOFF_') }},{% elif v.type == 'blob' %}
            {{ string(df.format) }},
            {{ literal(df.value|default(None)) }},{% endif %}
        )
{%- if df.callback %}

        @self.vector_{{ v.name|lower }}_{{ df.name|lower }}.on
        def _on_{{ v.name|lower }}_{{ df.name|lower }}_changed({% if v.type == 'blob' %}size, buff{% else %}new_value, old_value{% endif %}):

            return self.on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed({% if v.type == 'blob' %}size, buff{% else %}new_value, old_value{% endif %})
{%- endif %}
{%- endfor %}

        self.vector_{{ v.name|lower }} = nyx.{{ vector_class(v.type) }}(
            self.name(),
            {{ string(v.name) }},
            {{ enum(v.state, 'NyxState', 'NYX_STATE_') }},{% if v.type not in ('light', 'stream') %}
            {{ enum(v.perm, 'NyxPerm', 'NYX_PERM_') }},{% endif %}{% if v.type == 'switch' %}
            {{ enum(v.rule, 'NyxRule', 'NYX_RULE_') }},{% endif %}
            [
{%- for df in v.defs %}
                self.vector_{{ v.name|lower }}_{{ df.name|lower }},
{%- endfor %}
            ],{% if (v.group|default('')|trim)|length > 0 %}
            group = {{ string(v.group|trim) }},{% endif %}{% if (v.label|default('')|trim)|length > 0 %}
            label = {{ string(v.label|trim) }},{% endif %}{% if (v.hints|default('')|trim)|length > 0 %}
            hints = {{ string(v.hints|trim) }},{% endif %}{% if (v.message|default('')|trim)|length > 0 %}
            message = {{ string(v.message|trim) }},{% endif %}{% if v.timeout|default(None) is not none %}
            timeout = {{ v.timeout }},{% endif %}
        )
{%- if v.callback and v.type != 'stream' %}

        @self.vector_{{ v.name|lower }}.on
        def _on_{{ v.name|lower }}_changed(modified):

            self.on{{ v.name|pascalcase }}Changed(modified)
{%- endif %}
{%- if device.disabled|default(false) or v.disabled|default(false) %}

        self.vector_{{ v.name|lower }}.disabled = True
{%- endif %}
{%- endfor %}

        ################################################################################################################

    ####################################################################################################################

    def name(self) -> str:

        return {{ string(device.name) }}

    ####################################################################################################################

    def vectors(self) -> list:

        return [
{%- for v in device.vectors %}
            self.vector_{{ v.name|lower }},
{%- endfor %}
        ]

    ####################################################################################################################

    @property
    def node(self) -> nyx.NyxNode:

        return self._node

    ####################################################################################################################

    def initialize(self, _node) -> None:

        pass

    ####################################################################################################################

    def finalize(self, _node) -> None:

        pass
{%- for v in device.vectors %}
{%- for df in v.defs if df.callback %}

    ####################################################################################################################

    def on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(self, {% if v.type == 'blob' %}_size, _buff{% else %}_new_value, _old_value{% endif %}) -> bool:

        return True
{%- endfor %}
{%- if v.callback and v.type != 'stream' %}

    ####################################################################################################################

    def on{{ v.name|pascalcase }}Changed(self, _modified) -> None:

        pass
{%- endif %}
{%- endfor %}

########################################################################################################################
'''[1:]

        for device in self._devices:

            filename = os.path.join(self._driver_path, 'autogen', f'glue_{device["name"].lower()}.py')

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self._render(
                    template,
                    device = device
                ))

    ####################################################################################################################

    def _generate_devices(self) -> None:

        template = '''
# -*- coding: utf-8 -*-
########################################################################################################################

from .autogen.glue_{{ device.name|lower }} import Device{{ device.name|pascalcase }}Glue

########################################################################################################################

class Device{{ device.name|pascalcase }}(Device{{ device.name|pascalcase }}Glue):

    ####################################################################################################################

    def __init__(self):

        super().__init__()

    ####################################################################################################################

    def initialize(self, _node) -> None:

        pass

    ####################################################################################################################

    def finalize(self, _node) -> None:

        pass
{%- for v in device.vectors %}
{%- for df in v.defs if df.callback %}

    ####################################################################################################################

    def on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(self, {% if v.type == 'blob' %}_size, _buff{% else %}_new_value, _old_value{% endif %}) -> bool:

        return True
{%- endfor %}
{%- if v.callback and v.type != 'stream' %}

    ####################################################################################################################

    def on{{ v.name|pascalcase }}Changed(self, _modified) -> None:

        pass
{%- endif %}
{%- endfor %}

########################################################################################################################
'''[1:]

        for device in self._devices:

            filename = os.path.join(self._driver_path, f'device_{device["name"].lower()}.py')

            if self._override_device or not os.path.isfile(filename):

                with open(filename, 'wt', encoding = 'utf-8') as f:

                    f.write(self._render(
                        template,
                        device = device
                    ))

    ####################################################################################################################

    def _generate_credentials(self) -> None:

        template = '''
# -*- coding: utf-8 -*-
########################################################################################################################
# !!! AUTOGENERATED FILE !!!                                                                                           #
########################################################################################################################

MQTT_USERNAME = {% if descr.enableMQTT %}{{ string(descr.mqttUsername) }}{% else %}None{% endif %}
MQTT_PASSWORD = {% if descr.enableMQTT %}{{ string(descr.mqttPassword) }}{% else %}None{% endif %}

########################################################################################################################
'''[1:]

        filename = os.path.join(self._driver_path, 'credentials.py')

        with open(filename, 'wt', encoding = 'utf-8') as f:

            f.write(self._render(
                template
            ))

    ####################################################################################################################

    def _generate_init(self) -> None:

        template = '''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
########################################################################################################################

import nyx
import signal
import argparse

from .credentials import MQTT_PASSWORD, MQTT_USERNAME
{%- for d in devices %}
from .device_{{ d.name|lower }} import Device{{ d.name|pascalcase }}
{%- endfor %}

########################################################################################################################

def main() -> int:

    ####################################################################################################################

    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--indi-url', default = {% if descr.enableINDI %}{{ string(descr.indiURL) }}{% else %}None{% endif %})
    parser.add_argument('-m', '--mqtt-url', default = {% if descr.enableMQTT %}{{ string(descr.mqttURL) }}{% else %}None{% endif %})
    parser.add_argument('-s', '--stream-url', default = {% if descr.enableNSS %}{{ string(descr.nssURL) }}{% else %}None{% endif %})

    parser.add_argument('-u', '--mqtt-username', default = MQTT_USERNAME)
    parser.add_argument('-p', '--mqtt-password', default = MQTT_PASSWORD)

    parser.add_argument('-t', '--node-timeout', type = int, default = {{ descr.nodeTimeout }})

    args = parser.parse_args()

    ####################################################################################################################

    devices = [
{%- for d in devices %}
        Device{{ d.name|pascalcase }}(),
{%- endfor %}
    ]

    vector_list = [
        vector
        for device in devices
        for vector in device.vectors()
    ]

    ####################################################################################################################

    nyx.nyx_set_log_level(nyx.NyxLogLevel.INFO)

    ####################################################################################################################

    stop = False

    def signal_handler(_signo, _frame):

        nonlocal stop

        stop = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    ####################################################################################################################

    with nyx.NyxNode(
        {{ string(descr.nodeName) }},
        vector_list,
        args.indi_url,
        args.mqtt_url,
        args.stream_url,
        args.mqtt_username,
        args.mqtt_password,
        3000,
        True,
    ) as node:

        initialized_devices = []

        try:

            for device in devices:
            
                device._node = node

                device.initialize(node)

                initialized_devices.append(device)

            while not stop:

                node.poll(args.node_timeout)

        finally:

            for device in reversed(initialized_devices):

                device.finalize(node)

    ####################################################################################################################

    print('Bye.')

    return 0

########################################################################################################################
'''[1:]

        filename = os.path.join(self._driver_path, '__init__.py')

        if self._override_main or not os.path.isfile(filename):

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self._render(
                    template,
                    devices = self._devices
                ))

    ####################################################################################################################

    def _generate_main(self) -> None:

        template = '''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
########################################################################################################################
# !!! AUTOGENERATED FILE !!!                                                                                           #
########################################################################################################################

from . import main

########################################################################################################################

SystemExit(main())

########################################################################################################################
'''[1:]

        filename = os.path.join(self._driver_path, '__main__.py')

        if self._override_main or not os.path.isfile(filename):

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self._render(
                    template,
                    devices = self._devices
                ))

########################################################################################################################
