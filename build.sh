#!/bin/bash

########################################################################################################################

THIS_SCRIPT=${BASH_SOURCE[0]:-$0}

while [[ -n $(readlink "${THIS_SCRIPT}") ]]
do
  THIS_SCRIPT=$(readlink "${THIS_SCRIPT}")
done

NYX_GEN_HOME=$(cd "$(dirname "${THIS_SCRIPT}")" && pwd)/

########################################################################################################################

NYX_GEN_HOST=$(rustc -Vv | grep '^host:' | cut -f 2 -d ' ')

if [[ -z "${NYX_GEN_HOST}" ]]
then
  echo 'Rust is not installed!'

  exit 1
fi

########################################################################################################################

(
  cd ${NYX_GEN_HOME} || exit 1

  rm -fr "${NYX_GEN_HOME}/spec/"
  rm -fr "${NYX_GEN_HOME}/work/"

  PYTHONPATH="${NYX_GEN_HOME}" pyinstaller \
--onefile \
--noconfirm \
--distpath "${NYX_GEN_HOME}/bin/" \
--specpath "${NYX_GEN_HOME}/spec/" \
--workpath "${NYX_GEN_HOME}/work/" \
--name "nyx-gen-${NYX_GEN_HOST}" \
"${NYX_GEN_HOME}/bin/nyx-gen"
)

########################################################################################################################

# For Nyx Assistant

if [[ -d "${NYX_GEN_HOME}/../src-tauri/binaries/" ]]
then
  echo "Copying '${NYX_GEN_HOME}/bin/nyx-gen-${NYX_GEN_HOST}' to '${NYX_GEN_HOME}/../src-tauri/binaries/'"
 
  cp "${NYX_GEN_HOME}/bin/nyx-gen-${NYX_GEN_HOST}" "${NYX_GEN_HOME}/../src-tauri/binaries/"
fi

########################################################################################################################

exit 0

########################################################################################################################
