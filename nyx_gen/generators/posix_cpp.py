# -*- coding: utf-8 -*-
########################################################################################################################

import os

########################################################################################################################

from ..abstract_generator import AbstractGenerator, generator_config

########################################################################################################################

@generator_config(name = 'posix-c++', null = 'nullptr', src_ext = 'cpp', head_ext = 'hpp')
class PosixCppGenerator(AbstractGenerator):

    ####################################################################################################################

    def __init__(self, args, descr):

        super().__init__(args, descr)

    ####################################################################################################################

    def generate(self) -> None:

        self._generate_cmake()
        self._generate_device_headers()
        self._generate_device_glue_sources()
        self._generate_device_sources()
        self._generate_driver_headers()
        self._generate_driver_sources()
        self._generate_credentials()
        self._generate_main()

    ####################################################################################################################
    # CMAKE
    ####################################################################################################################

    def _generate_cmake(self) -> None:

        template = '''
########################################################################################################################

cmake_minimum_required(VERSION 3.5)

########################################################################################################################

project({{ descr.nodeName|lower }} CXX)

set(CMAKE_CXX_STANDARD 17)

add_compile_options(-Wall -Wno-unknown-pragmas -Wno-unused-function -O3)

########################################################################################################################

find_package(NyxNode REQUIRED)

########################################################################################################################

set(SOURCE_FILES
{%- for d in devices %}
    ./src/device_{{ d.name|lower }}.{{ src_ext }}
{%- endfor %}
    ./src/driver.{{ src_ext }}
    ./src/main.{{ src_ext }}
)

########################################################################################################################

add_executable({{ descr.nodeName|lower }} ${SOURCE_FILES})

target_include_directories({{ descr.nodeName|lower }} PRIVATE ${NYXNODE_INCLUDE_DIR} ./include)

target_link_libraries({{ descr.nodeName|lower }} PRIVATE ${NYXNODE_{{ 'STATIC' if descr.static else 'SHARED' }}_LIB_PATH})

########################################################################################################################
'''[1:]

        filename = os.path.join(self._driver_path, 'CMakeLists.txt')

        if self._override_cmake or not os.path.isfile(filename):

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self.render(
                    template,
                    descr = self._descr,
                    devices = self._devices
                ))

    ####################################################################################################################

    def _generate_device_headers(self) -> None:

        template = '''
/*--------------------------------------------------------------------------------------------------------------------*/

#ifndef NYX_{{ descr.nodeName|upper }}_DEVICE_{{ device.name|upper }}_{{ head_ext|upper }}
#define NYX_{{ descr.nodeName|upper }}_DEVICE_{{ device.name|upper }}_{{ head_ext|upper }}

/*--------------------------------------------------------------------------------------------------------------------*/

#include <nyx_node.hpp>

/*--------------------------------------------------------------------------------------------------------------------*/

namespace nyx_{{ descr.nodeName|lower }} {

/*--------------------------------------------------------------------------------------------------------------------*/

class Device_{{ device.name|lower }} : public Nyx::BaseDevice
{
public:
    /*----------------------------------------------------------------------------------------------------------------*/

    Device_{{ device.name|lower }}();

    ~Device_{{ device.name|lower }}();

    /*----------------------------------------------------------------------------------------------------------------*/

    STR_t name() const override
    {
        return "{{ device.name }}";
    }

    /*----------------------------------------------------------------------------------------------------------------*/
{%  for v in device.vectors -%}
{%-   for df in v.defs if df.callback %}

{%-     if   v.type == 'number' and 'd' in df.format %}
    void on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, int value, bool modified);
{%-     elif v.type == 'number' and 'l' in df.format %}
    void on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, long value, bool modified);
{%-     elif v.type == 'number' and 'f' in df.format %}
    void on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, double value, bool modified);
{%-     elif v.type == 'text' %}
    void on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, STR_t value, bool modified);
{%-     elif v.type == 'switch' %}
    void on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, nyx_onoff_t value, bool modified);
{%-     elif v.type == 'light' %}
    void on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, nyx_state_t value, bool modified);
{%-     endif %}
{%-   endfor %}
{%-   if v.callback %}
    void on_{{ v.name|lower }}_changed(nyx_object_t *vector, bool modified);
{%-   endif %}
{% endfor %}
    /*----------------------------------------------------------------------------------------------------------------*/

private:
    /*----------------------------------------------------------------------------------------------------------------*/

    void initialize() override;

    void finalize() override;

    /*----------------------------------------------------------------------------------------------------------------*/
{%  for v in device.vectors -%}
{%-   for df in v.defs if df.callback %}
    static void _{{ v.name|lower }}_{{ df.name|lower }}_callback(nyx_object_t *def_vector, bool modified);
{%-   endfor -%}
{%-   if v.callback %}
    static void _{{ v.name|lower }}_callback(nyx_object_t *vector, bool modified);
{%-   endif %}
{% endfor %}
    /*----------------------------------------------------------------------------------------------------------------*/
};

/*--------------------------------------------------------------------------------------------------------------------*/

} /* namespace nyx_{{ descr.nodeName|lower }} */

/*--------------------------------------------------------------------------------------------------------------------*/

#endif /* NYX_{{ descr.nodeName|upper }}_DEVICE_{{ device.name|upper }}_{{ head_ext|upper }} */

/*--------------------------------------------------------------------------------------------------------------------*/
'''[1:]

        for device in self._devices:

            filename = os.path.join(self._driver_path, 'include', f'device_{device["name"].lower()}.{self._head_ext}')

            if self._override_device or not os.path.isfile(filename):

                with open(filename, 'wt', encoding = 'utf-8') as f:

                    f.write(self.render(
                        template,
                        descr = self._descr,
                        device = device
                    ))

    ####################################################################################################################

    def _generate_device_glue_sources(self) -> None:

        template = '''
/* !!! AUTOGENERATED FILE !!! */
/*--------------------------------------------------------------------------------------------------------------------*/
{%  for v in device.vectors %}
{%-   for df in v.defs %}
static nyx_dict_t *s_vector_def_{{ device.name|lower }}_{{ v.name|lower }}_{{ df.name|lower }} = {{ null }};
{%-   endfor %}
static nyx_dict_t *s_vector_{{ device.name|lower }}_{{ v.name|lower }} = {{ null }};
{% endfor %}
/*--------------------------------------------------------------------------------------------------------------------*/
/* DEF VECTOR CALLBACKS                                                                                               */
/*--------------------------------------------------------------------------------------------------------------------*/
{%- for v in device.vectors %}
{%-   for df in v.defs if df.callback %}

void Device_{{ device.name|lower }}::_{{ v.name|lower }}_{{ df.name|lower }}_callback(nyx_object_t *def_vector, bool modified)
{
    Device_{{ device.name|lower }} *self = (Device_{{ device.name|lower }} *) def_vector->ctx;

    if(self != {{ null }})
    {
{%-     if   v.type == 'number' and 'd' in df.format %}
        int value = nyx_number_def_get_int((nyx_dict_t *) def_vector);
        self->on_{{ v.name|lower }}_{{ df.name|lower }}_changed(def_vector, value, modified);
{%-     elif v.type == 'number' and 'l' in df.format %}
        long value = nyx_number_def_get_long((nyx_dict_t *) def_vector);
        self->on_{{ v.name|lower }}_{{ df.name|lower }}_changed(def_vector, value, modified);
{%-     elif v.type == 'number' and 'f' in df.format %}
        double value = nyx_number_def_get_double((nyx_dict_t *) def_vector);
        self->on_{{ v.name|lower }}_{{ df.name|lower }}_changed(def_vector, value, modified);
{%-     elif v.type == 'text' %}
        STR_t value = nyx_text_def_get((nyx_dict_t *) def_vector);
        self->on_{{ v.name|lower }}_{{ df.name|lower }}_changed(def_vector, value, modified);
{%-     elif v.type == 'switch' %}
        nyx_onoff_t value = nyx_switch_def_get((nyx_dict_t *) def_vector);
        self->on_{{ v.name|lower }}_{{ df.name|lower }}_changed(def_vector, value, modified);
{%-     elif v.type == 'light' %}
        nyx_state_t value = nyx_light_def_get((nyx_dict_t *) def_vector);
        self->on_{{ v.name|lower }}_{{ df.name|lower }}_changed(def_vector, value, modified);
{%-     endif %}
    }
}
{%-   endfor %}
{%- endfor %}

/*--------------------------------------------------------------------------------------------------------------------*/
/* VECTOR CALLBACKS                                                                                                   */
/*--------------------------------------------------------------------------------------------------------------------*/
{%- for v in device.vectors if v.callback %}

void Device_{{ device.name|lower }}::_{{ v.name|lower }}_callback(nyx_object_t *vector, bool modified)
{
    Device_{{ device.name|lower }} *self = (Device_{{ device.name|lower }} *) vector->ctx;

    if(self != {{ null }})
    {
        self->on_{{ v.name|lower }}_changed(vector, modified);
    }
}
{%- endfor %}

/*--------------------------------------------------------------------------------------------------------------------*/

void Device_{{ device.name|lower }}::initialize()
{
{%- for v in device.vectors %}
    /*----------------------------------------------------------------------------------------------------------------*/
    /* VECTOR {{ device.name|upper }}::{{ v.name|upper }} */
    /*----------------------------------------------------------------------------------------------------------------*/
{%    for df in v.defs %}

{%-     if v.type == 'number' %}
    s_vector_def_{{ device.name|lower }}_{{ v.name|lower }}_{{ df.name|lower }} = nyx_number_def_new("{{ df.name }}", "{{ df.label }}", "{{ df.format }}", {{ df.min }}, {{ df.max }}, {{ df.step }}, {{ df.value }});
{%-     elif v.type == 'text' %}
    s_vector_def_{{ device.name|lower }}_{{ v.name|lower }}_{{ df.name|lower }} = nyx_text_def_new("{{ df.name }}", "{{ df.label }}", "{{ df.value }}");
{%-     elif v.type == 'light' %}
    s_vector_def_{{ device.name|lower }}_{{ v.name|lower }}_{{ df.name|lower }} = nyx_light_def_new("{{ df.name }}", "{{ df.label }}", {{ df.value }});
{%-     elif v.type == 'switch' %}
    s_vector_def_{{ device.name|lower }}_{{ v.name|lower }}_{{ df.name|lower }} = nyx_switch_def_new("{{ df.name }}", "{{ df.label }}", {{ df.value }});
{%-     elif v.type == 'blob' %}
    s_vector_def_{{ device.name|lower }}_{{ v.name|lower }}_{{ df.name|lower }} = nyx_blob_def_new("{{ df.name }}", "{{ df.label }}", {{ df.value }});
{%-     elif v.type == 'stream' %}
    s_vector_def_{{ device.name|lower }}_{{ v.name|lower }}_{{ df.name|lower }} = nyx_stream_def_new("{{ df.name }}", "{{ df.label }}");
{%-     endif %}
{%-     if df.callback %}
    s_vector_def_{{ device.name|lower }}_{{ v.name|lower }}_{{ df.name|lower }}->base.in_callback = _{{ v.name|lower }}_{{ df.name|lower }}_callback;
{%-     endif %}
    s_vector_def_{{ device.name|lower }}_{{ v.name|lower }}_{{ df.name|lower }}->base.ctx = (void *) this;
{%    endfor %}
    /*----------------------------------------------------------------------------------------------------------------*/

    nyx_dict_t *{{ device.name|lower }}_{{ v.name|lower }}_defs[] = {
{%-     for df in v.defs %}
        s_vector_def_{{ device.name|lower }}_{{ v.name|lower }}_{{ df.name|lower }},
{%-    endfor %}
        {{ null }},
    };

    /*----------------------------------------------------------------------------------------------------------------*/

    nyx_opts_t {{ device.name|lower }}_{{ v.name|lower }}_opts = {
        .label = {% if (v.label|default('')|trim)|length > 0 %}"{{ v.label|trim }}"{% else %}{{ null }}{% endif %},
        .group = {% if (v.group|default('')|trim)|length > 0 %}"{{ v.group|trim }}"{% else %}{{ null }}{% endif %},
        .timeout = {{ v.timeout|default(0, true) }},
        .message = {% if (v.message|default('')|trim)|length > 0 %}"{{ v.message|trim }}"{% else %}{{ null }}{% endif %},
    };

    /*----------------------------------------------------------------------------------------------------------------*/
{%    if v.type == 'number' %}
    s_vector_{{ device.name|lower }}_{{ v.name|lower }} = nyx_number_def_vector_new(
        "{{ device.name }}",
        "{{ v.name }}",
        {{ v.state }},
        {{ v.perm }},
        {{ device.name|lower }}_{{ v.name|lower }}_defs,
        &{{ device.name|lower }}_{{ v.name|lower }}_opts
    );
{%    elif v.type == 'text' %}
    s_vector_{{ device.name|lower }}_{{ v.name|lower }} = nyx_text_def_vector_new(
        "{{ device.name }}",
        "{{ v.name }}",
        {{ v.state }},
        {{ v.perm }},
        {{ device.name|lower }}_{{ v.name|lower }}_defs,
        &{{ device.name|lower }}_{{ v.name|lower }}_opts
    );
{%    elif v.type == 'light' %}
    s_vector_{{ device.name|lower }}_{{ v.name|lower }} = nyx_light_def_vector_new(
        "{{ device.name }}",
        "{{ v.name }}",
        {{ v.state }},
        {{ device.name|lower }}_{{ v.name|lower }}_defs,
        &{{ device.name|lower }}_{{ v.name|lower }}_opts
    );
{%    elif v.type == 'switch' %}
    s_vector_{{ device.name|lower }}_{{ v.name|lower }} = nyx_switch_def_vector_new(
        "{{ device.name }}",
        "{{ v.name }}",
        {{ v.state }},
        {{ v.perm }},
        {{ v.rule }},
        {{ device.name|lower }}_{{ v.name|lower }}_defs,
        &{{ device.name|lower }}_{{ v.name|lower }}_opts
    );
{%    elif v.type == 'blob' %}
    s_vector_{{ device.name|lower }}_{{ v.name|lower }} = nyx_blob_def_vector_new(
        "{{ device.name }}",
        "{{ v.name }}",
        {{ v.state }},
        {{ v.perm }},
        {{ device.name|lower }}_{{ v.name|lower }}_defs,
        &{{ device.name|lower }}_{{ v.name|lower }}_opts
    );
{%    elif v.type == 'stream' %}
    s_vector_{{ device.name|lower }}_{{ v.name|lower }} = nyx_stream_def_vector_new(
        "{{ device.name }}",
        "{{ v.name }}",
        {{ v.state }},
        {{ device.name|lower }}_{{ v.name|lower }}_defs,
        &{{ device.name|lower }}_{{ v.name|lower }}_opts
    );
{%   endif %}
{%- if v.callback %}
    s_vector_{{ device.name|lower }}_{{ v.name|lower }}->base.in_callback = _{{ v.name|lower }}_callback;
{%-  endif %}
{%- if device.disabled|default(false) or v.disabled|default(false) %}
    s_vector_{{ device.name|lower }}_{{ v.name|lower }}->base.flags |= NYX_FLAGS_DISABLED;
{%-   endif %}
    s_vector_{{ device.name|lower }}_{{ v.name|lower }}->base.ctx = (void *) this;

    /*----------------------------------------------------------------------------------------------------------------*/

    this->registerVector(s_vector_{{ device.name|lower }}_{{ v.name|lower }});
{% endfor %}
    /*----------------------------------------------------------------------------------------------------------------*/
}

/*--------------------------------------------------------------------------------------------------------------------*/

void Device_{{ device.name|lower }}::finalize()
{
    /* DO NOTHING  */
}

/*--------------------------------------------------------------------------------------------------------------------*/
'''[1:]

        for device in self._devices:

            filename = os.path.join(self._driver_path, 'src', 'autogen', f'glue_{device["name"].lower()}')

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self.render(
                    template,
                    descr = self._descr,
                    device = device
                ))

    ####################################################################################################################
    # src/device_<Device>.cpp
    ####################################################################################################################

    def _generate_device_sources(self) -> None:

        template = '''
/*--------------------------------------------------------------------------------------------------------------------*/

#include "../include/device_{{ device.name|lower }}.{{ head_ext }}"

/*--------------------------------------------------------------------------------------------------------------------*/

namespace nyx_{{ descr.nodeName|lower }} {

/*--------------------------------------------------------------------------------------------------------------------*/

#include "./autogen/glue_{{ device.name|lower }}"

/*--------------------------------------------------------------------------------------------------------------------*/

Device_{{ device.name|lower }}::Device_{{ device.name|lower }}()
{
    this->initialize();

    /* TO BE IMPLEMENTED */
}

/*--------------------------------------------------------------------------------------------------------------------*/

Device_{{ device.name|lower }}::~Device_{{ device.name|lower }}()
{
    this->finalize();

    /* TO BE IMPLEMENTED */
}

/*--------------------------------------------------------------------------------------------------------------------*/
{%- for v in device.vectors -%}
{%-   for df in v.defs if df.callback %}
{%      if   v.type == 'number' and 'd' in df.format %}
void Device_{{ device.name|lower }}::on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, int value, bool modified)
{%-     elif v.type == 'number' and 'l' in df.format %}
void Device_{{ device.name|lower }}::on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, long value, bool modified)
{%-     elif v.type == 'number' and 'f' in df.format %}
void Device_{{ device.name|lower }}::on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, double value, bool modified)
{%-     elif v.type == 'text' %}
void Device_{{ device.name|lower }}::on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, STR_t value, bool modified)
{%-     elif v.type == 'switch' %}
void Device_{{ device.name|lower }}::on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, nyx_onoff_t value, bool modified)
{%-     elif v.type == 'light' %}
void Device_{{ device.name|lower }}::on_{{ v.name|lower }}_{{ df.name|lower }}_changed(nyx_object_t *def_vector, nyx_state_t value, bool modified)
{%-     endif %}
{
    /* TO BE IMPLEMENTED */
}

/*--------------------------------------------------------------------------------------------------------------------*/
{%-   endfor -%}
{%-   if v.callback %}

void Device_{{ device.name|lower }}::on_{{ v.name|lower }}_changed(nyx_object_t *vector, bool modified)
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
                        descr = self._descr,
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

    void initialize() override;

    /*----------------------------------------------------------------------------------------------------------------*/

    STR_t name() const override
    {
        return "{{ descr.nodeName }}";
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    STR_t tcpURI() const override;

    STR_t mqttURI() const override;
    STR_t mqttUsername() const override;
    STR_t mqttPassword() const override;

    STR_t redisURI() const override;
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

        with open(filename, 'wt', encoding = 'utf-8') as f:

            f.write(self.render(
                template,
                descr = self._descr
            ))

    ####################################################################################################################
    # src/driver.cpp  (implémentation de Driver)
    ####################################################################################################################

    def _generate_driver_sources(self) -> None:

        template = '''
/*--------------------------------------------------------------------------------------------------------------------*/

#include "../include/driver.{{ head_ext }}"
{%- for d in devices %}
#include "../include/device_{{ d.name|lower }}.{{ head_ext }}"
{%- endfor %}

/*--------------------------------------------------------------------------------------------------------------------*/

#include "credentials.{{ head_ext }}"

/*--------------------------------------------------------------------------------------------------------------------*/

namespace nyx_{{ descr.nodeName|lower }} {

/*--------------------------------------------------------------------------------------------------------------------*/

void Driver::initialize()
{
{%- for d in devices %}
    this->registerDevice(std::unique_ptr<Nyx::BaseDevice>(new Device_{{ d.name|lower }}()));
{%- endfor %}
}

/*--------------------------------------------------------------------------------------------------------------------*/

STR_t Driver::tcpURI() const
{
    return {%- if descr.enableTCP %} "{{ descr.tcpURI }}" {%- else %} {{ null }} {%- endif %};
}

/*--------------------------------------------------------------------------------------------------------------------*/

STR_t Driver::mqttURI() const
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

STR_t Driver::redisURI() const
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

        with open(filename, 'wt', encoding = 'utf-8') as f:

            f.write(self.render(
                template,
                descr = self._descr,
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
                template,
                descr = self._descr
            ))

    ####################################################################################################################

    def _generate_main(self) -> None:

        template = '''
/*--------------------------------------------------------------------------------------------------------------------*/

#include "../include/driver.{{ head_ext }}"

/*--------------------------------------------------------------------------------------------------------------------*/

int main()
{
    nyx_set_log_level(NYX_LOG_LEVEL_INFO);

    nyx_{{ descr.nodeName|lower }}::Driver driver;

    return driver.run();
}

/*--------------------------------------------------------------------------------------------------------------------*/
'''[1:]

        filename = os.path.join(self._driver_path, 'src', f'main.{self._src_ext}')

        if self._override_main or not os.path.isfile(filename):

            with open(filename, 'wt', encoding = 'utf-8') as f:

                f.write(self.render(
                    template,
                    descr = self._descr,
                    devices = self._devices
                ))

########################################################################################################################
