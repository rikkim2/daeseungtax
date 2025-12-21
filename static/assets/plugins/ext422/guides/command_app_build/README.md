# Inside The App Build Process

The build script provided by [Sencha Cmd](http://www.sencha.com/products/sencha-cmd/) is
the component that ties together and automates the many low-level features of Sencha Cmd
(such as the Compiler). There is rarely a one-size-fits-all solution for builds so the
build script provides many options to configure and customize its behavior. This guide will
explain the principles behind the build script and where you might look should you need to
tailor the build process to suit your needs.

## Prerequisites

The following guides are recommended reading before proceeding further:

  - [Introduction to Sencha Cmd](#!/guide/command).
  - [Using Sencha Cmd](#!/guide/command_app).

## Introduction

Internally, the `sencha app build` command does basic validation and calls in to the
[Apache Ant](http://ant.apache.org/) build script found in `"build.xml"` at the root of
the application. Specifically, it calls the `"build"` target of this script. This means
the entire build process can be examined, extended and (if necessary) even modified.

Because `sencha app build` simply invokes the `"build"` target of the Ant `"build.xml"`
file, you can equivalently invoke a build directly from Ant. This can be useful in IDE's
like Eclipse and NetBeans for invoking your builds but also in a Continuous Integration
server that understands Ant (which is just about all of them).

The generated `"build.xml"` is a minimal Ant script that uses an Ant `import` task to
import `".sencha/app/build-impl.xml"` as well as several other files. While `"build.xml"`
is intended to be edited after it is generated, the `".sencha/app/*-impl.xml" files are
not. These files will be replaced by `sencha app upgrade` and so should be edited unless
absolutely necessary. These files are, however, an excellent  reference but should be modified
unless necessary.

## Build Targets

The targets below define the application build process from start to finish. With the
exception of `init` each target has a property that can be set to 1 to disable that step.

  * init
  * refresh
  * resolve (defaults to 1; set skip.resolve=0 to enable)
  * js
  * resources
  * sass
  * slice
  * page
  * native-package

With the exception of `init` each of these targets can be dropped out of the default build
by use of a build property (see below) with the target name prefixed by `"skip."`. For
example, to disable the `slice` target:

    skip.slice=1

These steps can also be run individually if only that piece is desired. This is often the
useful for rebuilding only the Sass:

    sencha ant sass

*Note:* Using `sencha ant` is equivalent to using your own version of Ant if you have Ant
1.8 or higher installed.

## Configuration

Most aspects of the build script behind `sencha app build` are controlled by properties as
is typical of Ant. In this case there are two kinds of properties: configuration properties
and build properties.

### Configuration Properties

Sencha Cmd configuration properties are available to the build script but also drive many
other features of Sencha Cmd (like the compiler). To see the current set of configuration
properties, run this command:

    sencha diag show

In most cases you can tell where each property comes from by its prefix:

  * `app.`  -- See `"app.json"` and `".sencha/app/sencha.cfg"`.
  * `workspace.` -- See `"workspace.json"` and `".sencha/workspace/sencha.cfg"`.
  * `framework.` -- See `"cmd/sencha.cfg"` in the Ext JS or Sencha Touch SDK.
  * `cmd.` -- See `"sencha.cfg"` in the Sencha Cmd install folder.

The use of configuration properties is much broader than the build process and is discussed
in some detail in [Advanced Sencha Cmd](#!/guide/command_advanced).

### Build Properties

The build script defines many other properties that are specific to builds. These build
properties are typically prefixed by `"build."`.

To see the current values of these you can run this command from your app folder:

    sencha ant .props

#### Setting Build Properties

There are many ways to configure build properties. The simplest way is to edit one of the
build properties files. To decide which file to edit it is helpful to know the priority of
each of these files and under what conditions they are loaded.

  * `"local.properties"` -- If present, this file is loaded first. This file is intended
  to be applied only locally (to the local machine). It should not be committed to source
  control to be used by others. These settings take priority over any properties defined
  in other properties files as well as the current configuration properties.
  * *Sencha Cmd configuration properties*
  * `".sencha/app/${build.environment}.properties"` -- Based on the value of the
  `build.environment` properties, exactly one of the following will be loaded. Setting
  properties in these files allow you to have different values for properties based on
  the type of build being run.
    * `".sencha/app/native.properties"`
    * `".sencha/app/package.properties"`
    * `".sencha/app/production.properties"`
    * `".sencha/app/testing.properties"`
  * `".sencha/app/build.properties"` -- These properties are loaded next and have lower
  priority over the build-environment-specific properties. These are properties that are
  used by all (or most) environments. This file is intended for customization.
  * `".sencha/app/defaults.properties"` -- These properties are the last (default) values
  to load. This file is "owned" by Sencha Cmd and will be updated each release as new
  properties are added. This file serves as a reference for the defined set of build
  properties but should not be edited; edit any of the other files instead.

The only properties that have higher priority than `"local.properties"` are those passed
in via the command line.

## Customization

Many common needs are accounted for via build properties, but it is impossible to account
for all use cases in this way. When configuration options cannot accomplish the task, the
next level of customization is to extend the generated `"build.xml"` Ant script.

In addition to the `import` task, `"build.xml"` contains a comment block describing many of
the available extension points. These are in the form of optional Ant targets and are named
after their build process step but with prefixes of `"-before-"` and `"-after-"`. The most
common extensions point then are these:

  * init
    * -before-init
    * -after-init
  * refresh
    * -before-refresh
    * -after-refresh
  * resolve
    * -before-resolve
    * -after-resolve
  * js
    * -before-js
    * -after-js
  * resources
    * -before-resources
    * -after-resources
  * sass
    * -before-sass
    * -after-sass
  * slice
    * -before-slice
    * -after-slice
  * page
    * -before-page
    * -after-page
  * native-package
    * -before-native-package
    * -after-native-package

To perform additional processing before or after any build step, add an appropriately named
target to `"build.xml"`. These targets will be invoked by `sencha app build`. These will also
be invoked if you use Ant to directly invoke a particular target.

One common use of these extensions points is to post-process the build output in the
`"all-classes.js"` file. Using a few predefined Ant tasks we can, for example, put a
copyright header on the generated file after it is generated:

    <target name="-after-page">
        <tstamp>
            <format property="THISYEAR" pattern="yyyy"/>
        </tstamp>

        <!--
        The build.classes.file property holds the full path to the "all-classes.js"
        file so we use that variable rather than hard-code the name.
        -->
        <move file="${build.classes.file}" tofile="${build.classes.file}.tmp"/>

        <concat destfile="${build.classes.file}">
            <header filtering="no" trimleading="yes">
    /*
     * Copyright (C) ${THISYEAR}. All Rights Reserved.
     * My Company Name
     */
            </header>
            <fileset file="${build.classes.file}.tmp"/>
        </concat>

        <delete file="${build.classes.file}.tmp" />
    </target>

## Next Steps

 - [Sencha Compiler Reference](#!/guide/command_compiler)
 - [Advanced Sencha Cmd](#!/guide/command_advanced)
