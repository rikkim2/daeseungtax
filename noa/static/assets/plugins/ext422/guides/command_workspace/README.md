# Workspaces in Sencha Cmd

This guide introduces the Workspace feature of [Sencha Cmd](http://www.sencha.com/products/sencha-cmd/).
Workspaces are designed to support multiple pages that need to share frameworks, packages
and other code.

## Prerequisites

The following guides are recommended reading before proceeding further:

  - [Introduction to Sencha Cmd](#!/guide/command).
  - [Using Sencha Cmd](#!/guide/command_app).

## What's a Workspace?

The process for building a large application starts the same as the process for building
single-page applications. Once an application expands to require multiple pages, certain
common issues arise:

  - Use of a common copies of the Sencha frameworks (Ext JS and/or Sencha Touch).
  - Use of code common across pages.
  - Shared or third-party packages.

To support these, Sencha Cmd defines the concept of a "Workspace". A Workspace is simply a
folder that ultimately contains one or more pages, frameworks, packages and other shared
code or files. The location of the Workspace root folder should be chosen to facilitate
these needs as well as your source control requirements. Any generated applications/pages
created in sub-folders of the Workspace folder regardless of their depth are consider to
be members of the Workspace.

Though not a requirement, it is typically the case that the Workspace folder is the root
folder in a source control repository.

The exact organization of your pages inside your Workspace is not important to Sencha Cmd.
For the sake of simplicity, however, the examples in this guide create all pages as immediate
sub-folders of the Workspace.

*Note on terminology.* Sencha frameworks-based applications, which employ MVC architecture,
call `Ext.application` at the top of the code tree. This can be confusing because these
frameworks use the term "application" to describe each page. In single-page applications,
these terms are interchangeable. When your application involves multiple pages, however,
this is not the case. This guide uses the term "page" in most cases because that is more
fitting in this context.

## Generating a Workspace

To generate a Workspace, use this command:

    sencha generate workspace /path/to/workspace

This will create the following structure in the specified folder.

    .sencha/                # Sencha-specific files (e.g. configuration)
        workspace/          # Workspace-specific content (see below)
            sencha.cfg      # Configuration file for Sencha Cmd
            plugin.xml      # Plugin for Sencha Cmd

The above directory structure should be familiar as it was part of the structure created
for single-page applications. In this case, however, only the ".sencha/workspace"
folder is created.

## Configuration

Configuration is similar to that for applications. The file `".sencha/app/sencha.cfg"`
holds configuration for one page ("app").

Unlike the single-page application, the `".sencha/workspace/sencha.cfg"` file is now useful
for setting configuration properties for all pages in the Workspace.

### Framework Locations

The location of Sencha Ext JS or Sencha Touch (i.e., the "SDK" or "framework") is stored
as a configuration property of the Workspace. This allows multiple pages to share this
configuration. Different teams will have different preferences on these locations and
whether or not the Sencha SDK's are stored in their source control system. The settings
discussed below give you control over the location of Sencha SDK's in your Workspace.

By default, a Workspace that has both Sencha Ex JS and Sencha Touch SDK's will have these
property settings in `".sencha/workspace/sencha.cfg"`:

    ext.dir=${workspace.dir}/ext
    touch.dir=${workspace.dir}/touch

The value of the `workspace.dir` property is determined by Sencha Cmd and is expanded as
needed. In other words, by default, a Workspace contains a copy of the SDK's used by the
applications it holds.

Applications reference their framework indirectly using the `app.framework` property in
their `".sencha/app/sencha.cfg"` file:

    app.framework=ext

## Generating Pages

Once you have a Workspace, generating pages ("apps") is the same as before:

    sencha -sdk /path/to/ext generate app ExtApp /path/to/workspace/extApp

You can also generate Sencha Touch applications in the same workspace:

    sencha -sdk /path/to/touch generate app TouchApp /path/to/workspace/touchApp

Because the target of these generated pages is in a Workspace, the following structure
will be created (which is slightly different than for a single-page app):

    .sencha/                    # Sencha-specific files (e.g. configuration)
        workspace/              # Workspace-specific content (see below)
            sencha.cfg          # Workspace's configuration file for Sencha Cmd
            plugin.xml          # Workspace plugin for Sencha Cmd

    ext/                        # A copy of the Ext JS SDK
        ...

    touch/                      # A copy of the Sencha Touch SDK
        ...

    extApp/
        .sencha/                # Sencha-specific files (e.g. configuration)
            app/                # Application-specific content
                sencha.cfg      # Application's configuration file for Sencha Cmd

    touchApp/
        .sencha/                # Sencha-specific files (e.g. configuration)
            app/                # Application-specific content
                sencha.cfg      # Configuration file for Sencha Cmd

    build/                      # The folder where build output is placed.
        production/             # Build output for production
            touchApp/
            extApp/
        testing/                # Build output for testing
            touchApp/
            extApp/

To generate more pages, repeat the above command.

## Building Pages

The process for building each page of a multi-page application is to run this command
from each of the appropriate folders:

    sencha app build

For efficiency, you can create a script for this process, perhaps using Sencha Cmd's
[Ant Integration](#!/guide/command_ant).

## Sharing Code Between Pages

When applications scale to multiple pages it is critical to have efficient means to share
code between them. There are two choices for doing this in a Workspace:

  - Packages
  - `workspace.classpath`

### Packages

Sencha Cmd provides a powerful package management subsystem that can be used to download
and integrate packages of JavaScript, Sass and resources into your applications. This was
discussed in the single-page application guides, but in the context of a Workspace, these
packages are simply shared. They are downloaded only once and are stored, by default, in
the `"./packages"` folder of the Workspace.

To change the location of shared packages, you can change `workspace.packages.dir` in the
`".sencha/workspace/sencha.cfg"` file.

### `workspace.classpath`

When shared JavaScript code is needed by multiple pages of an application and not by other
applications outside the Workspace, you can use this configuration option to automatically
include source folders in all applications. This property tells Sencha Cmd to scan these
shared code folders during a `sencha app build` command. Here's how to do that.

Let's add a `common` folder to the Workspace, like so:

    .sencha/
        workspace/
        ...
    common/             # Folder for common things between pages.
        src/            # Folder for common JavaScript code for all pages.

To include `common/src` when building all pages in the application, add the follow to
`".sencha/workspace/sencha.cfg"`:

    workspace.classpath=${workspace.dir}/common/src

This adds the following component to the default classpath:

    ${framework.classpath},${workspace.classpath},${app.classpath}

## Mixed Applications

Beyond sharing code between multiple Ext JS pages, or between multiple Sencha Touch
applications, there is often the need to share code across the two Sencha frameworks.
While the frameworks have a lot in common, they differ in many significant aspects,
particularly in the areas of UI components and layouts, which one would expect given that
they target such different device environments. Even with these differences, it's possible
to share code between the two frameworks, for example, sharing code between two model
class definitions.

In some cases, however, if you have a mixed application Workspace, you may need to isolate
your common code by framework. One way to do this is to set the `workspace.classpath` like
this:

    workspace.classpath=${workspace.dir}/common/src,${workspace.dir}/common/src-${framework.name}

With this definition, the Workspace would look like this:

    .sencha/
        workspace/
        ...
    common/             # Folder for common things between pages.
        src/            # Folder for common JavaScript code for all pages.
        src-ext/        # Folder for common JavaScript code for Ext JS pages.
        src-touch/      # Folder for common JavaScript code for Sencha Touch pages.

## Next Steps

 - [Compiler-Friendly Code Guidelines](#!/guide/command_code)
 - [Sencha Cmd Packages](#!/guide/command_packages)
 - [Advanced Sencha Cmd](#!/guide/command_advanced)
