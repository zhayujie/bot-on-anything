#!/usr/bin/env bash

set -x

# @see https://stackoverflow.com/questions/30003570/how-to-use-gnu-sed-on-mac-os-10-10-brew-install-default-names-no-longer-su
# @see https://www.cnblogs.com/fnlingnzb-learner/p/10657285.html
cmd=sed
if [ "$(uname)" == "Darwin" ];then
  brew install gnu-sed
  cmd=gsed
fi

echo "current sed command is: $cmd"

echo "allow http nopasword"
$cmd -i "s/\"http_auth_password\": \".*\"/\"http_auth_password\": \"\"/" config.json 
