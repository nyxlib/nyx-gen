# -*- coding: utf-8 -*-
########################################################################################################################

import os

########################################################################################################################

from ..abstract_generator import AbstractGenerator, generator_config

########################################################################################################################

@generator_config(name = 'posix-c++', null = 'nullptr', src_ext = 'cpp', head_ext = 'hpp')
class PosixCPPGenerator(AbstractGenerator):

    ####################################################################################################################

    def __init__(self, args, descr):

        super().__init__(args, descr)

    ####################################################################################################################

    def generate(self) -> None:

        self._generate_cmake()
        self._generate_device_headers()
        self._generate_glue_source()
        self._generate_device_sources()
        self._generate_driver_headers()
        self._generate_driver_sources()
        self._generate_credentials()
        self._generate_main()

    ####################################################################################################################

    def _generate_cmake(self) -> None:

        template = '''
########################################################################################################################

cmake_minimum_required(VERSION 3.5)

########################################################################################################################

project({{ descr.nodeName|lower }} CXX)

set(CMAKE_CXX_STANDARD 17)

add_compile_options(-Wall -Wno-unknown-pragmas -Wno-unused-function -O0 -g)

########################################################################################################################

find_package(NyxNode REQUIRED)

########################################################################################################################

set(SOURCE_FILES
{%- for d in devices %}
    ./src/autogen/glue_{{ d.name|lower }}.{{ src_ext }}
    ./src/device_{{ d.name|lower }}.{{ src_ext }}
{%- endfor %}
    ./src/driver.{{ src_ext }}
    ./src/main.{{ src_ext }}
)

########################################################################################################################

add_executable({{ descr.nodeName|lower }} ${SOURCE_FILES})

target_include_directories({{ descr.nodeName|lower }} PRIVATE ${NYXNODE_INCLUDE_DIR} ./include)

target_link_libraries({{ descr.nodeName|lower }} PRIVATE NyxNode::nyx-node-{{ 'static' if descr.static else 'shared' }})

########################################################################################################################
'''[1:]

        filename = os.path.join(self._driver_path, 'CMakeLists.txt')

        if self._override_cmake or not os.path.isfile(filename):

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self.render(
                    template,
                    devices = self._devices
                ))

    ####################################################################################################################

    def _generate_device_headers(self) -> None:

        template = '''
/*--------------------------------------------------------------------------------------------------------------------*/

#ifndef NYX_{{ descr.nodeName|upper }}_{{ device.name|upper }}_{{ head_ext|upper }}
#define NYX_{{ descr.nodeName|upper }}_{{ device.name|upper }}_{{ head_ext|upper }}

/*--------------------------------------------------------------------------------------------------------------------*/

#include <nyx_node.hpp>
{%- if (device.additionalHeaders|default('')|trim)|length > 0 %}

{{ device.additionalHeaders|trim }}
{%- endif %}

/*--------------------------------------------------------------------------------------------------------------------*/

namespace nyx_{{ descr.nodeName|lower }} {

/*--------------------------------------------------------------------------------------------------------------------*/

class Device{{ device.name|pascalcase }} : public {% if (device.parentClass|default('')|trim)|length > 0 %}"{{ device.parentClass|trim }}"{% else %}Nyx::BaseDevice{% endif %}
{
public:
    /*----------------------------------------------------------------------------------------------------------------*/

    Device{{ device.name|pascalcase }}();

    /*----------------------------------------------------------------------------------------------------------------*/

    STR_t name() const override
    {
        return "{{ device.name }}";
    }

    /*----------------------------------------------------------------------------------------------------------------*/
{%  for v in device.vectors -%}
{%-   for df in v.defs if df.callback %}

{%-     if v.type == 'number' -%}
{%          set subtype = get_number_type(df.format) -%}
{%-         if subtype == NYX_NUMBER_INT %}
    bool on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, int newValue, int oldValue);
{%-         elif subtype == NYX_NUMBER_UINT %}
    bool on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, unsigned int newValue, unsigned int oldValue);
{%-         elif subtype == NYX_NUMBER_LONG %}
    bool on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, long newValue, long oldValue);
{%-         elif subtype == NYX_NUMBER_ULONG %}
    bool on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, unsigned long newValue, unsigned long oldValue);
{%-         elif subtype == NYX_NUMBER_DOUBLE %}
    bool on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, double newValue, double oldValue);
{%-         endif %}
{%-     elif v.type == 'text' %}
    bool on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, STR_t newValue, STR_t oldValue);
{%-     elif v.type == 'switch' %}
    bool on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, int newValue, int oldValue);
{%-     elif v.type == 'light' %}
    bool on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, int newValue, int oldValue);
{%-     elif v.type == 'blob' %}
    bool on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, size_t size, BUFF_t buff);
{%-     endif %}
{%-   endfor %}
{%-   if v.callback and v.type != 'stream' %}
    void on{{ v.name|pascalcase }}Changed(nyx_dict_t *vector, bool modified);
{%-   endif %}
{% endfor %}
    /*----------------------------------------------------------------------------------------------------------------*/

protected:
    /*----------------------------------------------------------------------------------------------------------------*/
{%  for v in device.vectors %}
{%-   for df in v.defs %}
    nyx_dict_t *vector_{{ v.name|lower }}_{{ df.name|lower }} = {{ null }};
{%-   endfor %}
    nyx_dict_t *vector_{{ v.name|lower }} = {{ null }};
{% endfor %}
    /*----------------------------------------------------------------------------------------------------------------*/

private:
    /*----------------------------------------------------------------------------------------------------------------*/

    void glueInitialize() override;

    /*----------------------------------------------------------------------------------------------------------------*/

    void initialize(nyx_node_t *node) override;

    void finalize(nyx_node_t *node) override;

    /*----------------------------------------------------------------------------------------------------------------*/
};

/*--------------------------------------------------------------------------------------------------------------------*/

} /* namespace nyx_{{ descr.nodeName|lower }} */

/*--------------------------------------------------------------------------------------------------------------------*/

#endif /* NYX_{{ descr.nodeName|upper }}_{{ device.name|upper }}_{{ head_ext|upper }} */

/*--------------------------------------------------------------------------------------------------------------------*/
'''[1:]

        for device in self._devices:

            filename = os.path.join(self._driver_path, 'include', f'device_{device["name"].lower()}.{self._head_ext}')

            if self._override_device or not os.path.isfile(filename):

                with open(filename, 'wt', encoding = 'utf-8') as f:

                    f.write(self.render(
                        template,
                        device = device
                    ))

    ####################################################################################################################

    def _generate_glue_source(self) -> None:

        template = '''
/* !!! AUTOGENERATED FILE !!! */
/*--------------------------------------------------------------------------------------------------------------------*/

#include "../../include/device_{{ device.name|lower }}.{{ head_ext }}"

/*--------------------------------------------------------------------------------------------------------------------*/

namespace nyx_{{ descr.nodeName|lower }} {

/*--------------------------------------------------------------------------------------------------------------------*/
/* PROPERTY CALLBACKS                                                                                                 */
/*--------------------------------------------------------------------------------------------------------------------*/
{%- for v in device.vectors -%}
{%-   for df in v.defs if df.callback -%}
{%-     if v.type == 'number' -%}
{%-         set subtype = get_number_type(df.format) -%}
{%-         if subtype == NYX_NUMBER_INT %}

static bool _{{ v.name|lower }}_{{ df.name|lower }}_callback(nyx_dict_t *vector, nyx_dict_t *def, int new_value, int old_value)
{%-         elif subtype == NYX_NUMBER_UINT %}

static bool _{{ v.name|lower }}_{{ df.name|lower }}_callback(nyx_dict_t *vector, nyx_dict_t *def, unsigned int new_value, unsigned int old_value)
{%-         elif subtype == NYX_NUMBER_LONG %}

static bool _{{ v.name|lower }}_{{ df.name|lower }}_callback(nyx_dict_t *vector, nyx_dict_t *def, long new_value, long old_value)
{%-         elif subtype == NYX_NUMBER_ULONG %}

static bool _{{ v.name|lower }}_{{ df.name|lower }}_callback(nyx_dict_t *vector, nyx_dict_t *def, unsigned long new_value, unsigned long old_value)
{%-         elif subtype == NYX_NUMBER_DOUBLE %}

static bool _{{ v.name|lower }}_{{ df.name|lower }}_callback(nyx_dict_t *vector, nyx_dict_t *def, double new_value, double old_value)
{%-         endif -%}
{%-     elif v.type == 'text' %}

static bool _{{ v.name|lower }}_{{ df.name|lower }}_callback(nyx_dict_t *vector, nyx_dict_t *def, STR_t new_value, STR_t old_value)
{%-     elif v.type == 'switch' %}

static bool _{{ v.name|lower }}_{{ df.name|lower }}_callback(nyx_dict_t *vector, nyx_dict_t *def, int new_value, int old_value)
{%-     elif v.type == 'light' %}

static bool _{{ v.name|lower }}_{{ df.name|lower }}_callback(nyx_dict_t *vector, nyx_dict_t *def, int new_value, int old_value)
{%-     elif v.type == 'blob' %}

static bool _{{ v.name|lower }}_{{ df.name|lower }}_callback(nyx_dict_t *vector, nyx_dict_t *def, size_t size, BUFF_t buff)
{%-     endif %}
{
{%-     if v.type == 'blob' %}
    return static_cast<Device{{ device.name|pascalcase }} *>(vector->base.ctx)->on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(vector, def, size, buff);
{%-     else %}
    return static_cast<Device{{ device.name|pascalcase }} *>(vector->base.ctx)->on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(vector, def, new_value, old_value);
{%-     endif %}
}
{%-   endfor %}
{%- endfor %}

/*--------------------------------------------------------------------------------------------------------------------*/
/* VECTOR CALLBACKS                                                                                                   */
/*--------------------------------------------------------------------------------------------------------------------*/
{%- for v in device.vectors if v.callback and v.type != 'stream' %}

static void _{{ v.name|lower }}_callback(nyx_dict_t *vector, bool modified)
{
    Device{{ device.name|pascalcase }} *self = (Device{{ device.name|pascalcase }} *) vector->base.ctx;

    if(self != {{ null }})
    {
        self->on{{ v.name|pascalcase }}Changed(vector, modified);
    }
}
{%- endfor %}

/*--------------------------------------------------------------------------------------------------------------------*/
/* GLUE                                                                                                               */
/*--------------------------------------------------------------------------------------------------------------------*/

void Device{{ device.name|pascalcase }}::glueInitialize()
{
{%- for v in device.vectors %}
    /*----------------------------------------------------------------------------------------------------------------*/
    /* VECTOR {{ device.name|upper }}::{{ v.name|upper }} */
    /*----------------------------------------------------------------------------------------------------------------*/
{%    for df in v.defs -%}
{%-     if v.type == 'number' -%}
{%-         set subtype = get_number_type(df.format) -%}
{%-         if subtype == NYX_NUMBER_INT %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }} = nyx_number_prop_new_int("{{ df.name }}", {% if (df.label|default('')|trim)|length > 0 %}"{{ df.label|trim }}"{% else %}{{ null }}{% endif %}, "{{ df.format }}", {{ df.min }}, {{ df.max }}, {{ df.step }}, {{ df.value }});
{%-         elif subtype == NYX_NUMBER_UINT %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }} = nyx_number_prop_new_uint("{{ df.name }}", {% if (df.label|default('')|trim)|length > 0 %}"{{ df.label|trim }}"{% else %}{{ null }}{% endif %}, "{{ df.format }}", {{ df.min }}, {{ df.max }}, {{ df.step }}, {{ df.value }});
{%-         elif subtype == NYX_NUMBER_LONG %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }} = nyx_number_prop_new_long("{{ df.name }}", {% if (df.label|default('')|trim)|length > 0 %}"{{ df.label|trim }}"{% else %}{{ null }}{% endif %}, "{{ df.format }}", {{ df.min }}, {{ df.max }}, {{ df.step }}, {{ df.value }});
{%-         elif subtype == NYX_NUMBER_ULONG %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }} = nyx_number_prop_new_ulong("{{ df.name }}", {% if (df.label|default('')|trim)|length > 0 %}"{{ df.label|trim }}"{% else %}{{ null }}{% endif %}, "{{ df.format }}", {{ df.min }}, {{ df.max }}, {{ df.step }}, {{ df.value }});
{%-         elif subtype == NYX_NUMBER_DOUBLE %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }} = nyx_number_prop_new_double("{{ df.name }}", {% if (df.label|default('')|trim)|length > 0 %}"{{ df.label|trim }}"{% else %}{{ null }}{% endif %}, "{{ df.format }}", {{ df.min }}, {{ df.max }}, {{ df.step }}, {{ df.value }});
{%-         endif -%}
{%-     elif v.type == 'text' %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }} = nyx_text_prop_new("{{ df.name }}", {% if (df.label|default('')|trim)|length > 0 %}"{{ df.label|trim }}"{% else %}{{ null }}{% endif %}, "{{ df.value }}");
{%-     elif v.type == 'light' %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }} = nyx_light_prop_new("{{ df.name }}", {% if (df.label|default('')|trim)|length > 0 %}"{{ df.label|trim }}"{% else %}{{ null }}{% endif %}, {{ df.value }});
{%-     elif v.type == 'switch' %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }} = nyx_switch_prop_new("{{ df.name }}", {% if (df.label|default('')|trim)|length > 0 %}"{{ df.label|trim }}"{% else %}{{ null }}{% endif %}, {{ df.value }});
{%-     elif v.type == 'blob' %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }} = nyx_blob_prop_new("{{ df.name }}", {% if (df.label|default('')|trim)|length > 0 %}"{{ df.label|trim }}"{% else %}{{ null }}{% endif %}, "{{ df.format }}", {{ df.value }});
{%-     elif v.type == 'stream' %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }} = nyx_stream_prop_new("{{ df.name }}", {% if (df.label|default('')|trim)|length > 0 %}"{{ df.label|trim }}"{% else %}{{ null }}{% endif %});
{%-     endif %}
{%-     if df.callback -%}
{%-       if v.type == 'number' -%}
{%-           set subtype = get_number_type(df.format) -%}
{%            if subtype == NYX_NUMBER_INT %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }}->base.in_callback._int = _{{ v.name|lower }}_{{ df.name|lower }}_callback;
{%-           elif subtype == NYX_NUMBER_UINT %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }}->base.in_callback._uint = _{{ v.name|lower }}_{{ df.name|lower }}_callback;
{%-           elif subtype == NYX_NUMBER_LONG %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }}->base.in_callback._long = _{{ v.name|lower }}_{{ df.name|lower }}_callback;
{%-           elif subtype == NYX_NUMBER_ULONG %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }}->base.in_callback._ulong = _{{ v.name|lower }}_{{ df.name|lower }}_callback;
{%-           elif subtype == NYX_NUMBER_DOUBLE %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }}->base.in_callback._double = _{{ v.name|lower }}_{{ df.name|lower }}_callback;
{%-           endif %}
{%-       elif v.type == 'text' %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }}->base.in_callback._str = _{{ v.name|lower }}_{{ df.name|lower }}_callback;
{%-       elif v.type == 'light' %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }}->base.in_callback._int = _{{ v.name|lower }}_{{ df.name|lower }}_callback;
{%-       elif v.type == 'switch' %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }}->base.in_callback._int = _{{ v.name|lower }}_{{ df.name|lower }}_callback;
{%-       elif v.type == 'blob' %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }}->base.in_callback._blob = _{{ v.name|lower }}_{{ df.name|lower }}_callback;
{%-       endif -%}
{%-     endif %}
    this->vector_{{ v.name|lower }}_{{ df.name|lower }}->base.ctx = static_cast<void *>(this);
{%    endfor %}
    /*----------------------------------------------------------------------------------------------------------------*/

    static nyx_dict_t *{{ v.name|lower }}_props[] = {
{%-     for df in v.defs %}
        this->vector_{{ v.name|lower }}_{{ df.name|lower }},
{%-    endfor %}
        {{ null }},
    };

    /*----------------------------------------------------------------------------------------------------------------*/

    nyx_opts_t {{ v.name|lower }}_opts = {
        .group = {% if (v.group|default('')|trim)|length > 0 %}"{{ v.group|trim }}"{% else %}{{ null }}{% endif %},
        .label = {% if (v.label|default('')|trim)|length > 0 %}"{{ v.label|trim }}"{% else %}{{ null }}{% endif %},
        .hints = {% if (v.hints|default('')|trim)|length > 0 %}"{{ v.hints|trim }}"{% else %}{{ null }}{% endif %},
        .message = {% if (v.message|default('')|trim)|length > 0 %}"{{ v.message|trim }}"{% else %}{{ null }}{% endif %},
        .timeout = {{ v.timeout|default(0, true) }},
    };

    /*----------------------------------------------------------------------------------------------------------------*/
{%    if v.type == 'number' %}
    this->vector_{{ v.name|lower }} = nyx_number_vector_new(
        this->name(),
        "{{ v.name }}",
        {{ v.state }},
        {{ v.perm }},
        {{ v.name|lower }}_props,
        &{{ v.name|lower }}_opts
    );
{%    elif v.type == 'text' %}
    this->vector_{{ v.name|lower }} = nyx_text_vector_new(
        this->name(),
        "{{ v.name }}",
        {{ v.state }},
        {{ v.perm }},
        {{ v.name|lower }}_props,
        &{{ v.name|lower }}_opts
    );
{%    elif v.type == 'light' %}
    this->vector_{{ v.name|lower }} = nyx_light_vector_new(
        this->name(),
        "{{ v.name }}",
        {{ v.state }},
        {{ v.name|lower }}_props,
        &{{ v.name|lower }}_opts
    );
{%    elif v.type == 'switch' %}
    this->vector_{{ v.name|lower }} = nyx_switch_vector_new(
        this->name(),
        "{{ v.name }}",
        {{ v.state }},
        {{ v.perm }},
        {{ v.rule }},
        {{ v.name|lower }}_props,
        &{{ v.name|lower }}_opts
    );
{%    elif v.type == 'blob' %}
    this->vector_{{ v.name|lower }} = nyx_blob_vector_new(
        this->name(),
        "{{ v.name }}",
        {{ v.state }},
        {{ v.perm }},
        {{ v.name|lower }}_props,
        &{{ v.name|lower }}_opts
    );
{%    elif v.type == 'stream' %}
    this->vector_{{ v.name|lower }} = nyx_stream_vector_new(
        this->name(),
        "{{ v.name }}",
        {{ v.state }},
        {{ v.name|lower }}_props,
        &{{ v.name|lower }}_opts
    );
{%   endif %}
{%- if v.callback and v.type != 'stream' %}
    this->vector_{{ v.name|lower }}->base.in_callback._vector = _{{ v.name|lower }}_callback;
{%-  endif %}
{%- if device.disabled|default(false) or v.disabled|default(false) %}
    this->vector_{{ v.name|lower }}->base.flags |= NYX_FLAGS_DISABLED;
{%-   endif %}
    this->vector_{{ v.name|lower }}->base.ctx = static_cast<void *>(this);

    /*----------------------------------------------------------------------------------------------------------------*/

    this->registerVector(this->vector_{{ v.name|lower }});
{% endfor %}
    /*----------------------------------------------------------------------------------------------------------------*/
}

/*--------------------------------------------------------------------------------------------------------------------*/

} /* namespace nyx_{{ descr.nodeName|lower }} */

/*--------------------------------------------------------------------------------------------------------------------*/
'''[1:]

        for device in self._devices:

            filename = os.path.join(self._driver_path, 'src', 'autogen', f'glue_{device["name"].lower()}.{self._src_ext}')

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self.render(
                    template,
                    device = device
                ))

    ####################################################################################################################

    def _generate_device_sources(self) -> None:

        template = '''
/*--------------------------------------------------------------------------------------------------------------------*/

#include "../include/device_{{ device.name|lower }}.{{ head_ext }}"

/*--------------------------------------------------------------------------------------------------------------------*/

namespace nyx_{{ descr.nodeName|lower }} {

/*--------------------------------------------------------------------------------------------------------------------*/

Device{{ device.name|pascalcase }}::Device{{ device.name|pascalcase }}()
{
    this->glueInitialize();
}

/*--------------------------------------------------------------------------------------------------------------------*/

void Device{{ device.name|pascalcase }}::initialize(nyx_node_t *node)
{
    /* TO BE IMPLEMENTED */
}

/*--------------------------------------------------------------------------------------------------------------------*/

void Device{{ device.name|pascalcase }}::finalize(nyx_node_t *node)
{
    /* TO BE IMPLEMENTED */
}

/*--------------------------------------------------------------------------------------------------------------------*/
{%- for v in device.vectors -%}
{%-   for df in v.defs if df.callback -%}
{%-     if v.type == 'number' -%}
{%-         set subtype = get_number_type(df.format) -%}
{%-         if subtype == NYX_NUMBER_INT %}

bool Device{{ device.name|pascalcase }}::on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, int newValue, int oldValue)
{%-         elif subtype == NYX_NUMBER_UINT %}

bool Device{{ device.name|pascalcase }}::on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, unsigned int newValue, unsigned int oldValue)
{%-         elif subtype == NYX_NUMBER_LONG %}

bool Device{{ device.name|pascalcase }}::on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, long newValue, long oldValue)
{%-         elif subtype == NYX_NUMBER_ULONG %}

bool Device{{ device.name|pascalcase }}::on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, unsigned long newValue, unsigned long oldValue)
{%-         elif subtype == NYX_NUMBER_DOUBLE %}

bool Device{{ device.name|pascalcase }}::on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, double newValue, double oldValue)
{%-         endif %}
{%-     elif v.type == 'text' %}

bool Device{{ device.name|pascalcase }}::on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, STR_t newValue, STR_t oldValue)
{%-     elif v.type == 'switch' %}

bool Device{{ device.name|pascalcase }}::on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, int newValue, int oldValue)
{%-     elif v.type == 'light' %}

bool Device{{ device.name|pascalcase }}::on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, int newValue, int oldValue)
{%-     elif v.type == 'blob' %}

bool Device{{ device.name|pascalcase }}::on{{ v.name|pascalcase }}{{ df.name|pascalcase }}Changed(nyx_dict_t *vector, nyx_dict_t *def, size_t size, BUFF_t buff)
{%-     endif %}
{
    /* TO BE IMPLEMENTED */

    return true;
}

/*--------------------------------------------------------------------------------------------------------------------*/
{%-   endfor -%}
{%-   if v.callback and v.type != 'stream' %}

void Device{{ device.name|pascalcase }}::on{{ v.name|pascalcase }}Changed(nyx_dict_t *vector, bool modified)
{
    /* TO BE IMPLEMENTED */
}

/*--------------------------------------------------------------------------------------------------------------------*/
{%-   endif -%}
{%- endfor %}

} /* namespace nyx_{{ descr.nodeName|lower }} */

/*--------------------------------------------------------------------------------------------------------------------*/
'''[1:]

        for device in self._devices:

            filename = os.path.join(self._driver_path, 'src', f'device_{device["name"].lower()}.{self._src_ext}')

            if self._override_device or not os.path.isfile(filename):

                with open(filename, 'wt', encoding = 'utf-8') as f:

                    f.write(self.render(
                        template,
                        device = device
                    ))

    ####################################################################################################################

    def _generate_driver_headers(self) -> None:

        template = '''
/*--------------------------------------------------------------------------------------------------------------------*/

#ifndef NYX_{{ descr.nodeName|upper }}_DRIVER_{{ head_ext|upper }}
#define NYX_{{ descr.nodeName|upper }}_DRIVER_{{ head_ext|upper }}

/*--------------------------------------------------------------------------------------------------------------------*/

#include <nyx_node.hpp>

/*--------------------------------------------------------------------------------------------------------------------*/

namespace nyx_{{ descr.nodeName|lower }} {

/*--------------------------------------------------------------------------------------------------------------------*/

class Driver : public Nyx::BaseDriver
{
protected:
    /*----------------------------------------------------------------------------------------------------------------*/

    void glueInitialize() override;

    /*----------------------------------------------------------------------------------------------------------------*/

    STR_t name() const override
    {
        return "{{ descr.nodeName }}";
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    STR_t indiURL() const override;

    STR_t mqttURL() const override;
    STR_t mqttUsername() const override;
    STR_t mqttPassword() const override;

    STR_t redisURL() const override;
    STR_t redisUsername() const override;
    STR_t redisPassword() const override;

    int nodeTimeoutMS() const override;

    /*----------------------------------------------------------------------------------------------------------------*/
};

/*--------------------------------------------------------------------------------------------------------------------*/

} /* namespace nyx_{{ descr.nodeName|lower }} */

/*--------------------------------------------------------------------------------------------------------------------*/

#endif /* NYX_{{ descr.nodeName|upper }}_DRIVER_{{ head_ext|upper }} */

/*--------------------------------------------------------------------------------------------------------------------*/
'''[1:]

        filename = os.path.join(self._driver_path, 'include', f'driver.{self._head_ext}')

        if self._override_main or not os.path.isfile(filename):

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self.render(
                    template
                ))

    ####################################################################################################################

    def _generate_driver_sources(self) -> None:

        template = '''
/*--------------------------------------------------------------------------------------------------------------------*/

#include "../include/driver.{{ head_ext }}"

/*--------------------------------------------------------------------------------------------------------------------*/
{%  for d in devices %}
#include "../include/device_{{ d.name|lower }}.{{ head_ext }}"
{%- endfor %}

/*--------------------------------------------------------------------------------------------------------------------*/

#include "credentials.{{ head_ext }}"

/*--------------------------------------------------------------------------------------------------------------------*/

namespace nyx_{{ descr.nodeName|lower }} {

/*--------------------------------------------------------------------------------------------------------------------*/

void Driver::glueInitialize()
{
{%- for d in devices %}
    this->registerDevice(std::unique_ptr<Nyx::BaseDevice>(new Device{{ d.name|pascalcase }}()));
{%- endfor %}
}

/*--------------------------------------------------------------------------------------------------------------------*/

STR_t Driver::indiURL() const
{
    return {%- if descr.enableTCP %} "{{ descr.tcpURI }}" {%- else %} {{ null }} {%- endif %};
}

/*--------------------------------------------------------------------------------------------------------------------*/

STR_t Driver::mqttURL() const
{
    return {%- if descr.enableMQTT %} "{{ descr.mqttURI }}" {%- else %} {{ null }} {%- endif %};
}

/*--------------------------------------------------------------------------------------------------------------------*/

STR_t Driver::mqttUsername() const
{
    return MQTT_USERNAME;
}

/*--------------------------------------------------------------------------------------------------------------------*/

STR_t Driver::mqttPassword() const
{
    return MQTT_PASSWORD;
}

/*--------------------------------------------------------------------------------------------------------------------*/

STR_t Driver::redisURL() const
{
    return {%- if descr.enableRedis %} "{{ descr.redisURI }}" {%- else %} {{ null }} {%- endif %};
}

/*--------------------------------------------------------------------------------------------------------------------*/

STR_t Driver::redisUsername() const
{
    return REDIS_USERNAME;
}

/*--------------------------------------------------------------------------------------------------------------------*/

STR_t Driver::redisPassword() const
{
    return REDIS_PASSWORD;
}

/*--------------------------------------------------------------------------------------------------------------------*/

int Driver::nodeTimeoutMS() const
{
    return {{ descr.nodeTimeout }};
}

/*--------------------------------------------------------------------------------------------------------------------*/

} /* namespace nyx_{{ descr.nodeName|lower }} */

/*--------------------------------------------------------------------------------------------------------------------*/
'''[1:]

        filename = os.path.join(self._driver_path, 'src', f'driver.{self._src_ext}')

        if self._override_main or not os.path.isfile(filename):

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self.render(
                    template,
                    devices = self._devices
                ))

    ####################################################################################################################

    def _generate_credentials(self) -> None:

        template = '''
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

    ####################################################################################################################

    def _generate_main(self) -> None:

        template = '''
/*--------------------------------------------------------------------------------------------------------------------*/

#include "../include/driver.{{ head_ext }}"

/*--------------------------------------------------------------------------------------------------------------------*/

int main(int argc, char **argv)
{
    nyx_set_log_level(NYX_LOG_LEVEL_INFO);

    nyx_{{ descr.nodeName|lower }}::Driver driver;

    return driver.run(argc, argv);
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
