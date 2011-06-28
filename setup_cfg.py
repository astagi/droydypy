import os

#Compilation.
ANDROID_NDK_PATH = "/home/andrea/android-ndk-r5c/"
ANDROID_GCC_PATH = ANDROID_NDK_PATH + "toolchains/arm-linux-androideabi-4.4.3/prebuilt/linux-x86/bin/"
ANDROID_GCC_NAME = "arm-linux-androideabi-gcc"
ANDROID_LIB_REL = "platforms/android-9/arch-arm/usr/lib/"
ANDROID_INCLUDE_REL = "platforms/android-9/arch-arm/usr/include/"

#Installation.
ANDROID_SDK_PATH = "/home/andrea/android-sdk-linux_x86/"

#Setup.py.
ANDROID_GCC = ANDROID_GCC_PATH + ANDROID_GCC_NAME
ANDROID_LIB = ANDROID_NDK_PATH + ANDROID_LIB_REL
ANDROID_INCLUDE = ANDROID_NDK_PATH + ANDROID_INCLUDE_REL
ANDROID_ADB = os.path.join(ANDROID_SDK_PATH,"platform-tools","adb")
