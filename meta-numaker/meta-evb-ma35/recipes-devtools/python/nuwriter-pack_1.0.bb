SUMMARY = "Generate NuWriter pack.bin for MA35 Series SPI NAND programming"
require nuwriter-pack.inc

do_compile[depends] += " \
    tf-a-ma35:do_deploy \
    u-boot-ma35:do_deploy \
    linux-ma35:do_deploy \
    obmc-phosphor-image:do_image_complete \
"
