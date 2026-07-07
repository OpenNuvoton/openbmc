# Fix warning: "Group render has never been defined"
# meta-phosphor removes udev from USERADD_PACKAGES which skips render group creation.
# Re-add only the group definition on the udev package.
USERADD_PACKAGES:append = " udev"
GROUPADD_PARAM:udev = "-r render"
