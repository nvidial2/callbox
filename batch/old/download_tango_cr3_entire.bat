pushd \\serv2\home\gcflab\workspace\callbox-test_cr3\software\releases\core\cr3.br\tools
download_all.exe -v 3 -d COM26 --mass_storage=None --iso=None --customConfig=None VARIANT=tango-internal
popd
echo download > endBatch