# Introduction to Sencha Cmd

[Sencha Cmd](http://www.sencha.com/products/sencha-cmd/) is a cross-platform 
command line tool that provides many automated tasks around the full life-cycle
of your applications from generating a new project to deploying an application to
production.

## Understanding Sencha Cmd

Sencha Cmd provides a collection of powerful, time-saving features that
work together and in conjunction with the Sencha Ext JS and Sencha Touch frameworks.
Sencha Cmd provides the following capabilities:

 - **Code Generation Tools**: Code generation tools to generate entire applications and
 extend those applications with new MVC components.
 - **JS Compiler**: A framework-aware, JavaScript compiler that understands the semantics
 of Sencha frameworks and can produce minimal footprint builds from your source. The
 compiler can optimize many of the high-level semantics provided by Sencha frameworks to
 reduce load time of your applications.
 - **Web Server**: Provides a lightweight web server that serves files from localhost.
 - **Native Packaging**: Native packaging to convert a Sencha Touch application into a
 first-class, mobile application that has access to device functionality and can be
 distributed in App Stores.
 - **Package Management System**: Distributed package management system for easy integration
 of packages (such as Ext JS Themes) created by others or from the Sencha Package Repository.
 - **Build Scripts**: Generated build script for applications and packages with "before" and
 "after" extension points so you can customize the build process to fit your specific needs.
 - **Tuning Tools**: Powerful code selection tools for tuning what is included in your
 application's final build, determine common code across pages and partition shared code
 using high-level set operations to get builds exactly as you want them.
 - **Workspace Management**: Assists in sharing frameworks, packages and custom code across
 multiple applications.
 - **Image Capture**: Converts CSS3 features (such as border-radius and linear-gradient)
 into sprites for legacy browsers.
 - **Flexible Configuration System**: Enables defaults to be specified for command options
 at the application or workspace level or across all workspaces on a machine.
 - **Logging**: Robust logging to help you understand the inner workings of commands and facilitate
 troubleshooting.
 - **Third-party Software**: Sencha Cmd includes a compatible version of Compass, Sass, and 
 Apache Ant.
 - **Code Generation Hooks**: Can be specific to one page or shared by all pages in the
 workspace, for example, to check coding conventions or guidelines as new models are
 generated).

## Compatibility

Sencha Cmd supports Sencha Ext JS version 4.1.1a or higher and Sencha Touch version 2.1
or higher. Many of the features of Sencha Cmd require framework support that is only
available at these or later version levels. Some low-level commands can be used for older
versions of Sencha frameworks or JavaScript in general.

If you are using an older version of Ext JS, you may use Sencha Cmd's `build` command to
build via your JSB file. In other words, Sencha Cmd can replace JSBuilder to produce a
compressed build of the files described in a JSB file. Sencha Cmd will not update your JSB
file as was done by the deprecated SDK Tools v2. 

Sencha Touch 2.0 and Sencha Ext JS 4.0 require the deprecated 
[SDK Tools v2](http://www.sencha.com/products/sdk-tools), which cannot be used 
with later Touch or Ext JS versions.

<a name="SystemSetup"></a>
## System Setup

Download and install this software:

 - **JRE** Sencha Cmd requires 
   [Java Runtime Environment](http://www.oracle.com/technetwork/java/javase/downloads/jre7-downloads-1880261.html) 
   version 1.7 to support all functionality, however, most features will work with 1.6 (the
   minimum supported version).
 - [Sencha Cmd](http://www.sencha.com/products/sencha-cmd/)
 - **Ruby** Ruby differs by OS:
  - **Windows**: Download Ruby from [rubyinstaller.org](http://rubyinstaller.org/downloads/).
    Get the .exe file version of the software and install it.
  - **Mac OS**: Ruby is pre-installed. You can test if Ruby is installed with the 
    **Ruby -v** command. 
  - **Ubuntu**: Use **sudo apt-get install ruby2.0.0** to download Ruby.
 - **iOS Packaging**: Apple [Xcode](https://developer.apple.com/xcode/)
 - **Android Packaging**: [Android SDK Tools](http://developer.android.com/sdk/index.html) and [Eclipse](http://www.eclipse.org/) (optional).
 
Add the install paths to your PATH environmental variable.

### Verify Installation

To verify that Sencha Cmd is working properly, open a command line, change directory to
your application, and type the `sencha` command. 

You should see output that starts something like this:

    Sencha Cmd v4.0.n.n
    ...


## Upgrading Sencha Cmd

The `sencha upgrade` feature lets you upgrade Sencha Cmd.

Check for new updates to Sencha Cmd:

    sencha upgrade --check

Without the `--check` option, the `sencha upgrade` command downloads and installs the
latest version if you don't already have it:

    sencha upgrade

After the installer is done, start a new console or terminal to pick up the changes to
your PATH environment variable.

Because multiple versions of Sencha Cmd can be installed side-by-side, you can safely try
new releases and simply uninstall them (or adjust the PATH) to go back to your previous
version. Upgrading your applications using `sencha app upgrade` however, is something you
may need "roll back" if you downgrade to an older Sencha Cmd.

### Beta Releases

If you want to check for beta releases, use:

    sencha upgrade --check --beta

To install the latest beta version:

    sencha upgrade --beta

**Note** It is possible that the most current release is in either the "beta" or stable
channel. That is to say, `sencha upgrade --beta` may install a beta that predates the
current release that would be installed by `sencha upgrade`.

## Command Basics

Sencha Cmd features are arranged in categories (or modules) and commands:

    sencha [category] [command] [options...] [arguments...]

Help is available using the `help` command.

    sencha help [module] [action]

For example, try this:

    sencha help

Displays the current version and the available top-level commands. For example:

    Sencha Cmd v4.0.n.n
    ...

    Options
      * --background, -b - Runs the web server in a background thread
      * --cwd, -cw - Sets the directory from which commands should execute
      * --debug, -d - Sets log level to higher verbosity
      * --nologo, -n - Suppress the initial Sencha Cmd version display
      * --plain, -pl - enables plain logging output (no highlighting)
      * --quiet, -q - Sets log level to warnings and errors only
      * --sdk-path, -s - The location of the SDK to use for non-app commands
      * --time, -ti - Display the execution time after executing all commands

    Categories
      * app - Perform various application build processes
      * compass - Wraps execution of compass for sass compilation
      * compile - Compile sources to produce concatenated output and metadata
      * cordova - Manage Cmd/Cordova integration
      * fs - Utility commands to work with files
      * generate - Generates models, controllers, etc. or an entire application
      * manifest - Extract class metadata
      * package - Manages local and remote packages
      * phonegap - Manage Cmd/PhoneGap integration
      * repository - Manage local repository and remote repository connections
      * theme - Commands for low-level operations on themes
      * web - Manages a simple HTTP file server

    Commands
      * ant - Invoke Ant with helpful properties back to Sencha Cmd
      * build - Builds a project from a legacy JSB3 file.
      * config - Load a properties file or sets a configuration property
      * help - Displays help for commands
      * js - Executes arbitrary JavaScript file(s)
      * upgrade - Upgrades Sencha Cmd
      * which - Displays the path to the current version of Sencha Cmd

## Current Directory

In many cases, Sencha Cmd requires that you set a specific current directory. Or it may
just need to know details about the relevant Sencha SDK. The SDK can be determined
automatically by Sencha Cmd when it is run from a generated application folder or, for
some few commands, from an extracted SDK folder.

**Important** For the following commands, Sencha Cmd needs to be run from the root folder
of a generated application. The commands fail if not run from the application's root folder.

    * `sencha generate ...` (for commands other than `app`, `package` and `workspace`)
    * `sencha app ...`

This is also true of Packages. When running commands like `sencha package build`, the
current directory must be the desired package folder.

## Sencha Cmd Documentation

The many guides for Sencha Cmd are organized to help build on your understanding and it is
recommended that you follow this sequence. Jumping ahead can result in confusion as the
advanced guides often assume understanding of the content of the earlier guides.

At the start of each guide are links to any prerequisites for that guide. Further,
most guides end with a set of links for further reading.

## Beyond The Basics

There are many other details related to using Sencha Cmd that can be helpful. The `help`
command is a great reference, but if you want to walk through all the highlights, consult
[Advanced Sencha Cmd](#!/guide/command_advanced).

## Troubleshooting

Here are some tips for solving common problems encountered when using Sencha Cmd.

### Command Not Found

If running `sencha` results in the error message `sencha: command not found` on OSX/Linux
or `'sencha' is not recognized as an internal or external command, operable program or
batch file` on Windows, follow these steps:

- Close all existing terminal/command prompt windows and reopen them. 
- Make sure that Sencha Cmd is properly installed:
    - The installation directory exists. By default, the installation path is:
        - Windows: `C:\Users\Me\bin\Sencha\Cmd\{version}`
        - Mac OS X: `~/bin/Sencha/Cmd/{version}`
        - Linux: `~/bin/Sencha/Cmd/{version}`
    - The path to Sencha Cmd directory is prepended to your PATH environment variable.
      From the terminal, run `echo %PATH%` on Windows or `echo $PATH` on Mac or Linux.
      The Sencha Cmd directory should be displayed in part of the output. If this is not
      the case, add it to your PATH manually.
    - The environment variable `SENCHA_CMD_{version}` is set, with the value being
      the absolute path to the installation directory mentioned above. From the command
      line, use the **echo** command to view this variable. If the output is
      empty, set the environment variable manually. 

### Cannot find Ruby

If you see an error related to not recognizing or finding `"ruby"` this is likely because
Ruby is not installed or is not in your PATH. See the previous [System Setup](#SystemSetup)
section.

### Wrong Current Directory

A common mistake is to perform a command that requires the current directory to be either
an extracted SDK directory or an application directory, but such a directory has not been
set. If this requirement is not met, Sencha Cmd displays an error and exits.
	
Note that a valid application directory is one that was generated by Sencha Cmd.

### Errors While Resolving Dependencies

The `sencha app build` command works by reading your `index.html` and scanning for
required classes. If your application does not properly declare the classes it requires,
the build usually completes but will not contain all the classes needed by your application.

To ensure that you have all required classes specified, always develop with the debugger
console enabled ("Developer Tools" in IE/Chrome, FireBug in FireFox and Web Inspector in
Safari) and resolve all warnings and error messages as they appear.

Whenever you see a warning like this:

    [Ext.Loader] Synchronously loading 'Ext.foo.Bar'; consider adding 'Ext.foo.Bar' explicitly as a require of the corresponding class
	
Immediately add 'Ext.foo.Bar' inside the `requires` array property of the class from
which the dependency originates. If it is a application-wide dependency, add it to the
`requires` array property inside `Ext.application(...)` statement.

## Next Steps

 - [Using Sencha Cmd](#!/guide/command_app)
