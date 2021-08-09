#!/bin/bash
wget wget https://services.gradle.org/distributions/gradle-2.0-bin.zip
unzip gradle-2.0-bin.zip 
export PATH="$PWD/gradle-2.0/bin/:$PATH"
