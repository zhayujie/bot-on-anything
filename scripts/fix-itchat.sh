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

pack_dir="$(pip3 show itchat-uos | grep "Location" | awk '{print $2}')"
file_name="${pack_dir}/itchat/components/login.py"

sleep15Code="time.sleep(15)"

cat $file_name | grep $sleep15Code

if [ "$?" != "0" ];then
  echo "fix $sleep15Code"
  $cmd -i "/while not isLoggedIn/i\        $sleep15Code" $file_name
else
  echo "already fix $sleep15Code"
fi

sleep3Code="time.sleep(3)"

cat $file_name | grep $sleep3Code

if [ "$?" != "0" ];then
  echo "fix $sleep3Code"
  $cmd -i "s/elif status != '408'/elif status in ['408', '400']/" $file_name
  $cmd -i "/if isLoggedIn:/i\            time.sleep(3)" $file_name
else
  echo "already fix $sleep3Code"
fi
