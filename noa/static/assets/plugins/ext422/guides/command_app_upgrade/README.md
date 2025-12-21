# Understanding App Upgrade

This guide explains how to manage upgrades of [Sencha Cmd](http://www.sencha.com/products/sencha-cmd/)
and Sencha frameworks in your applications.

## Prerequisites

The following guides are recommended reading before proceeding further:

  - [Introduction to Sencha Cmd](#!/guide/command).
  - [Using Sencha Cmd](#!/guide/command_app).

## Upgrading Your Application

Generated applications include two basic kinds of content relevant to Sencha Cmd: build
scripts (or scaffolding) and the important content of the target Sencha SDK's. As such,
you will occasionally need to upgrade these pieces. You can do this with the following
command:

    sencha app upgrade [ path-to-new-framework ]

The "path-to-new-framework" is optional and is used to upgrade both the Sencha Cmd
scaffold *and* the framework used by the application.

### Preparing to Upgrade

When performing any bulk operation on your application source code, it is highly advisable
to start in a "clean" state with respect to version control. That is, it is best to have
no uncommitted changes before performing the upgrade. This way, you can easily review and
possibly discard changes made by `sencha app upgrade` with minimum trouble.

## Upgrading The Sencha Cmd Scaffold

To bring up a new version of Sencha Cmd with your application produced by a previous
version, you can run this command from inside your application:

    sencha app upgrade

This will replace the content of `".sencha"` but will also upgrade `"app.js"` as well as
a handful of other files.

## Upgrading Frameworks

Since generated applications include their own copies of the SDK from which they were
originally generated, applications need to be updated to use a new version of the SDK.
The `sencha app upgrade` command will replace the old SDK copy with the new one:

    sencha app upgrade ../downloads/ext-4.2.2

The above command points to the path to a downloaded and extracted SDK.

**Important.** Do not use the `-sdk` switch for this command as you would for the
`sencha generate app` command. Instead use the command shown above.

There may also be some changes made to generated source code if you are upgrading from
Ext JS 4.1 to 4.2+.

## Dealing With Merge Conflicts

In Sencha Cmd, the code generator incorporates a 3-way merge to best reconcile the
code it generates with the code it generated last time and the current state of the code
as you may have edited it. This approach allows you to edit files (like `"spp.js"`) in
many ways so long as your changes don't overlap those that Sencha Cmd wants to make.

The merge process follows this pseudo-code for `"app.js"` (as an example):

    mv app.js app.js.$old
    regenerate last version to app.js.$base
    generate new version to app.js
    diff3 app.js.$base app.js.$old app.js

In the ideal scenario, you won't notice this mechanism at work. There are situations,
however, in which you may receive an error message telling you there was a "Merge conflict"
and that you need to resolve this manually.

In cases where the base version cannot be recreated, the `".$old"` file is left on disk
and you can compare it to the current version. Or you can use your source control system
to compare the current file to what was last committed.

When the base version could be produced (the majority case), the `".$old"` file is deleted
because the conflicts are annotated in the target file in the standard way:

    <<<<<<< Generated
        // stuff that Sencha Cmd thinks belongs here
    =======
        // stuff that you have changed which conflicts
    >>>>>>> Custom

### Using Visual Merge Tools

This process exactly matches what you might expect in a source control system for a file
that you and another user (in this case, Sencha Cmd) have both modified. As with version
control, the ideal way to resolve these issues is with a visual merge tool.

To configure Sencha Cmd to invoke a merge tool when it encounters merge conflicts, you
need to set the following two properties:

    cmd.merge.tool
    cmd.merge.tool.args

Setting the `cmd.merge.tool` property can be as simple as a program name if that program
is in the PATH, but otherwise, it may need to be the full path to the executable.

The corresponding `cmd.merge.tool.args` property should be set according to the command
line arguments needed by the desired merge tool. This property is a template that can
contain the following replacement tokens:

    cmd.merge.tool.args={base} {user} {generated} {out}

The template is first split on spaces *then* the tokens are replaced by actual files names.
If the merge tool has more custom needs, it may be necessary to set `cmd.merge.tool` to a
shell script that can wrap the merge tool.

#### Merge Tool Helper Properties

Sencha Cmd provides properties to help configure several popular merge tools:

For [p4merge](http://www.perforce.com/product/components/perforce-visual-merge-and-diff-tools)
you can set these properties like so:

    cmd.merge.tool=p4merge
    cmd.merge.tool.args=${cmd.merge.tool.args.p4merge}

This assumes that `"p4merge"` is in your `PATH` environment variable. If not, you will need
to fully specify the path to the executable.

For [SourceGear](http://www.sourcegear.com/diffmerge/index.html):

    cmd.merge.tool.args=${cmd.merge.tool.args.sourcegear}

For [kdiff3](http://sourceforge.net/projects/kdiff3/files/kdiff3/):

    cmd.merge.tool.args=${cmd.merge.tool.args.kdiff3}

For Syntevo [SmartSynchronize 3](http://www.syntevo.com/smartsynchronize/index.html):

    cmd.merge.tool.args=${cmd.merge.tool.args.smartsync}

For [TortoiseMerge](http://tortoisesvn.net) (part of TortoiseSVN):

    cmd.merge.tool.args=${cmd.merge.tool.args.tortoise}

For [AraxisMerge](http://www.araxis.com/merge-overview.html):

    cmd.merge.tool.args=${cmd.merge.tool.args.araxis}

## Alternative Strategies

If you have heavily customized your application, it is sometimes simpler to just generate
a new application in a temporary location and start by copying its `".sencha"` folder to
replace your own, being careful to reconcile any changes you may have made and incorporate
them in the new version.

If you are using a workspace, you may need to copy the `".sencha/workspace"` folder from
the generated app to your workspace's `".sencha"` folder to replace the old version there.

## Next Steps

 - [Compiler-Friendly Code Guidelines](#!/guide/command_code)
 - [Sencha Cmd Packages](#!/guide/command_packages)
 - [Workspaces in Sencha Cmd](#!/guide/command_workspace)
 - [Advanced Sencha Cmd](#!/guide/command_advanced)
