---
title: firefoxos中往external添加一个新的可执行文件
date: 2018-08-07 17:21:53
tags:
---

其实这部分和安卓是完全一样的，在external目录下新建一个文件夹，test，然后新建一个test.c文件，随便写点测试代码。
主要的是需要编写一个Android.mk文件，如下
```
LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_ARM_MODE := arm
LOCAL_SRC_FILES := test.c
LOCAL_MODULE := test_readlnh
LOCAL_MODULE_TAGS := optional
LOCAL_MOUDLE_PATH := $(TARGET_OUT_EXECUTABLES)

include $(BUILD_EXECUTABLE)
```

之后先执行`. build/envsetup.sh`，然后`mmm external/test`即可。去out目录下找到生成的文件然后adb push到/data/local目录下，即可通过adb shell来执行该模块了。

这里要注意的是，执行`mmm`命令编译模块的时候，实际是依赖out目录下的某些文件的，有可能路径名会有问题，这种情况下把另一个目录下的lib复制过去就行了。这个问题没有看提示，瞎搞了半天，要引以为戒。