#!/bin/bash
#后台运行bot-on-anaything执行脚本

cd `dirname $0`/..
export BASE_DIR=`pwd`
echo $BASE_DIR

# check the nohup.out log output file
if [ ! -f "${BASE_DIR}/logs/log_info.log" ]; then
  mkdir "${BASE_DIR}/logs"
  touch "${BASE_DIR}/logs/log_info.log"
echo "${BASE_DIR}/logs/log_info.log"  
fi

nohup python3 "${BASE_DIR}/app.py" >> ${BASE_DIR}/logs/log_info.log  & tail -f "${BASE_DIR}/logs/log_info.log"

echo "bot-on-anaything is starting，you can check the ${BASE_DIR}/logs/log_info.log"

