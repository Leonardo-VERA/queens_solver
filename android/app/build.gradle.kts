import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

android {
    namespace = "com.leonardo.queens"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.leonardo.queens"
        minSdk = 30  // Android 11+ (personal app; the phone runs Android 16)
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
        ndk {
            // Snapdragon / all recent phones. Add "x86_64" to run in the emulator.
            abiFilters += listOf("arm64-v8a")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_17)
    }
}

chaquopy {
    defaultConfig {
        // OpenCV for Android (Chaquopy) exists for Python 3.10 only.
        version = "3.10"
        // Python 3.10 on the build machine. Auto-detected ("py -3.10" on
        // Windows); override with -Pqueens.buildPython=/path/to/python3.10
        (findProperty("queens.buildPython") as String?)?.let { buildPython(it) }
        pip {
            install("numpy==1.26.2")
            install("opencv-python-headless==4.5.1.48")
        }
    }
    sourceSets {
        getByName("main") {
            // The same recognition + solver code as the Streamlit app and the
            // Windows overlay: <repo>/src/queens.
            srcDir("../../src")
        }
    }
}
