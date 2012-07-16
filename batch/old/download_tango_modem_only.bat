pushd \\serv2.icerasemi.com\home\gcflab\workspace\callbox-test\software\main.br\tools
download_all.exe -v 3 -d COM33 --mass_storage=None --factory_tests=None --secondary_boot=None --loader=None --iso=None --customConfig=None --deviceConfig=None --productConfig=None --modem=modem-rsa-key0.zlib.wrapped ..\product\datacard\modem\build\dxp-tango-internal-obj\EV4
popd
echo download > endBatch
