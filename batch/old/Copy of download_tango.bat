pushd \\serv2.icerasemi.com\home\gcflab\workspace\callbox-test\software\main.br\tools
download_all.exe -v 3 -d COM26 --mass_storage=None --iso=None --customConfig=None VARIANT=tango-internal
popd
echo download > endBatch
