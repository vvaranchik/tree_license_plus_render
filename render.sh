#!/bin/bash

_filename='""'
_year='""'
_org_name='""'
_root='""'
_license=''

function is_abs() {
    arg=$1
    size=${#arg}
    if [ $size -gt 1 ];then
        if( [ ${arg:0:1} == '/' ] || [ ${arg:1:1} == ':' ] );then
            echo 1
        else
            echo 0
        fi
    else
        echo 0
    fi
}

function get_abs_filename() {
  echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
}

#process_arg "--filename=worker" "--year=2021" "--org_name=StackSoft" "--root_project=/path/to/project/" "/path/to/license/"
tmp=""
for i in "$@"; do
        case $i in
            --filename=*)
                tmp="${i#*=}"
                if [ "$tmp" != "" ];then
                    _filename="$tmp"
                fi
                shift
                ;;
            --year=*)
                tmp="${i#*=}"
                if [ "$tmp" != "" ];then
                _year="${i#*=}"
                fi
                shift
                ;;
            --org_name=*)
                tmp="${i#*=}"
                if [ "$tmp" != "" ];then
                _org_name="${i#*=}"
                fi
                shift
                ;;
            --root_folder=*)
                tmp="${i#*=}"
                if [ "$tmp" != "" ];then
                    _root="${i#*=}"
                fi
                shift
                ;;
            *) #this should be last parameter (path to license)
                tmp="${i}"
                if [ "$tmp" != "" ];then
                    _license="${i}"
                else
                    echo "No license file passed" 1>&2
                    exit 1
                fi
                shift
                break
                ;;
    esac
done

#echo "${_year}"
#echo "${_org_name}"
#echo "${_root}"
#echo "${_license}"
#echo "${_filename}"

isabs=$(is_abs "${_license}")
#echo "${isabs}"
if [ $isabs -ne 1 ];then
    _license=$(get_abs_filename $_license)
fi
#echo $_license
if [ -f $_license ];then
    license_content=`cat ${_license}`
    #echo "$license_content"
    license_content=$(echo "$license_content" | sed "s%{filename}%${_filename}%g")
    license_content=$(echo "$license_content" | sed "s%{year}%${_year}%g")
    license_content=$(echo "$license_content" | sed "s%{org_name}%${_org_name}%g")
    license_content=$(echo "$license_content" | sed "s%{root_folder}%${_root}%g")
    license_content=$(echo "$license_content" | tr -d '$')
    echo "${license_content}"
    #ls -a
else
    echo "License file '${_license}' not exist or license path was empty" 1>&2
    exit 1
fi
exit 0
