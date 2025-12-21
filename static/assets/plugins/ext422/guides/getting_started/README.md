# Getting Started

This guide helps you set up a development environment with all the required 
software tools you need to create and debug Ext JS applications. This guide
also explains the layout and directory contents of a standard application, 
and walks you through the creation of a simple application.

## Get Ext JS 4 SDK

Download [Ext JS 4 SDK](http://www.sencha.com/products/extjs/). Unzip the package 
into a new directory of your choosing. Because you may also be 
creating Touch applications 
as well, it's a good idea to place all available SDKs and their versions in a single 
directory for easy reference whenever you wish to create a new 
application (or upgrade older ones). 
In this case, an appropriate directory in which to place your SDKs can be called 
<code>SenchaSdk</code>, or any name you choose. 
The directory where you unzip Ext JS is the "<i>/path/to/extjs</i>" directory, which 
appears in the examples in this guide.

## Get a Web Browser

Ext JS 4 supports all major web browsers, from Internet Explorer 6 to the 
latest version of Google Chrome. During development, however, we recommend 
that you choose the latest version of the following browsers for the best debugging experience:

- [Google Chrome](http://www.google.com/chrome/) 
- [Apple Safari](http://www.apple.com/safari/download/) 
- [Mozilla Firefox](http://www.mozilla.com/en-US/firefox/fx/) with the [Firebug](http://getfirebug.com/) web development plugin

This tutorial assumes you are using the latest version of Google Chrome. 
If you don't already have Chrome take a moment to install it, and familiarize 
yourself with the 
[Chrome Developer Tools](http://code.google.com/chrome/devtools/docs/overview.html).

## Get Sencha Cmd

<a href="http://www.sencha.com/products/sencha-cmd/download">Sencha Cmd</a>
is a free tool with many useful functions. You can generate a starting environment, 
"stub" applications, update your software, update files, and it also provides a 
simplified web server. In addition, Sencha Cmd supports Ant commands 
that let you customize build tools.

<b>Note</b>: Ext JS 4.2.2 works with Sencha Cmd 4.0.0 and later.

After you download and install Sencha Cmd, you can verify that it's working by 
typing the <b>sencha</b> command in a command line prompt. The output appears as:

<pre>
$ sencha
<b>Sencha Cmd vn.n.n.n</b>
Sencha Cmd provides several categories of commands and some global switches. 
...
</pre>

<a name="scws"></a>
## Sencha Cmd Web Server

Sencha Cmd provides a simplified Jetty web server for use in serving your application
to your web browser. You can run the web server from a command line using the 
the <b>sencha web start</b> command.

You can set the port with the <code>-port</code> option. The
<code>-map</code> parameter specifies the path to the directory you want to serve.

By default, the server is accessed using the
<a href="http://localhost:1841">http://localhost:1841</a> URL in your browser.
The directory used for the root of the web server is the directory in which you issue
the <b>sencha web start</b> command.

The web server runs in the window until you press CTRL+c or open 
another command prompt and type the <b>sencha web stop</b> command. 

After completing the tutorial in this guide, you may want to use 
a more sophisticated web server such as the Apache HTTP web server. You 
can obtain a pre-configured Apache web server
using <a href="http://www.apachefriends.org/en/xampp.html">XAMPP</a>. 
Information on starting and stopping that web server, and where 
to put files that you access with the web server is
available at the XAMPP site. 

<a name"CreatingAnApp"></a>
## Creating an Application

After you install Ext JS, you can use the Sencha Cmd <code>generate</code> command to 
create the starting directory structure for your application. 

To create the "Hello Ext" application:

<ol>
<li><p>Choose or create a directory where your application will reside, 
change to that directory and issue the following command:</p>
<pre>
$ sencha -sdk <i>/path/to/extjs</i> generate app <i>MyApp</i> .
</pre>
<p>Where:</p>
<ol>
<li><i>/path/to/extjs</i> is the directory where you unzipped the Ext JS software.</li>
<li><i>MyApp</i> is the name you give your application.</li>
</ol></li>
<li><p>Now you're ready to write your application code. Open the 
<code>Application.js</code> file in the <code>app</code> directory, 
delete what's there, and insert the following code:</p>
<pre>
Ext.define('MyApp.Application', {
    name: 'MyApp',
    extend: 'Ext.app.Application',
    launch: function() {
        Ext.create('Ext.container.Viewport', {
            layout: 'fit',
            items: [
                {
                    title: 'Hello Ext',
                    html : 'Hello! Welcome to Ext JS.'
                }
            ]
        });
    }
});
</pre>
</li>
<li><p>We can now start up the Sencha web server to view our
application in a browser. If you have not already done so, open a command line
prompt and change directory to your <code>MyApp</code> directory.
Start the Sencha Cmd web server using the 
<b>sencha&nbsp;web&nbsp;start</b> command. 
These messages display:</p>
<pre>
$ <b>sencha web start</b>
Sencha Cmd vn.n.n.n
[INF] Starting shutdown listener socket
[INF] Listening for stop requests on: 62249
[INF] Mapping http://localhost:1841/ to ....
[INF] Starting http://localhost:1841
[INF] jetty-8.1.7.v20120910
[INF] NO JSP Support for /, did not find org.apache.jasper.servlet.JspServlet
[INF] started o.e.j.w.WebAppContext{/,file:/Users/me/Documents/MyApp/}
[INF] started o.e.j.w.WebAppContext{/,file:/Users/me/Documents/MyApp/}
[INF] Started SelectChannelConnector@0.0.0.0:1841
</pre>
</li>
<li><p>Open your browser and navigate to 
<a href="http://localhost:1841/">http://localhost:1841/</a>.
You should see a panel with a title bar containing the text "Hello Ext" 
and the "welcome" message in the panel's body area:</p>
{@img WelcomeToExtJS.png}
</li>
</ol>
<p>Success! You have created your first Ext JS application.</p>

## Behind the Scenes

Now that you've created your first application, let's look at what happened
as each step unfolded.

<ol>
<li><p>When you ran <b>sencha generate app</b>, Sencha Cmd 
created this list of files:</p>
<pre>
MyApp:
    .sencha    [Files used by Sencha CMD]
    app:       [Contains your application source]
        <b>Application.js</b> -- [The starting point of your app]
        controller:
            Main.js
            Readme.md
        model:
            Readme.md
        Readme.md
        store:
            Readme.md
        view:
            Main.js
            Readme.md
            Viewport.js
    app.js
    app.json
    bootstrap.css
    bootstrap.js
    bootstrap.json
    build:    [Where your testing, production, and native builds are generated]
        temp:
            production:
                MyApp:
                    sencha-compiler:
                        app:
                            full-page-master-bundle.js
                        cmd-packages.js
    build.xml
    ext: [Ext JS framework - do not modify]
        bootstrap.js
        build.xml
        builds:
            ext-*.js [Debugging files]
        cmd:
        ext-*.js [Debug and themes files]
        ext.js
        file-header.js
        license.txt
        locale:
            [Language source files]
        packages:
            [Locale &amp; themes directories]
        src:
            [Source files]
    index.html
    overrides: [Empty]
    packages: [Empty]
    Readme.md
    resources: [Empty]
    sass:
        config.rb
        etc: [Empty]
        example:
            bootstrap.css
            custom.js
            render.js
            theme.html
        src: [Empty]
        var: [Empty]
</pre>
</li>
<li><p>When you point your browser to the application directory, 
the browser opens your <code>index.html</code> file, 
loads the core Ext JS stylesheet, framework, and 
bootstrap code along with the <code>app.js</code> file. 
The <code>app.js</code> file contains the <code>Ext.application</code> class, 
which is the starting point for all applications. Because Sencha Cmd uses 
the <code>index.html</code> file to build production versions and 
because the generated content of this file is critical to the proper 
functioning of your application, do not edit this file.</p>

<pre>
&lt;!DOCTYPE HTML>
&lt;html>
&lt;head>
    &lt;meta charset="UTF-8">
    &lt;title>MyApp&lt;/title>
    &lt;!-- &lt;x-compile> -->
        &lt;!-- &lt;x-bootstrap> -->
            &lt;link rel="stylesheet" href="bootstrap.css">
            &lt;script src="ext/ext-dev.js">&lt;/script>
            &lt;script src="bootstrap.js">&lt;/script>
        &lt;!-- &lt;/x-bootstrap> -->
        &lt;script src="app.js">&lt;/script>
    &lt;!-- &lt;/x-compile> -->
&lt;/head>
&lt;body>&lt;/body>
&lt;/html>
</pre></li>
<li><p>The other important file generated by Sencha Cmd is <code>app.js</code>, 
the contents of which are shown here:</p>
<pre>
Ext.application({
    name: 'MyApp',
    extend: 'MyApp.Application',    
    autoCreateViewport: true
});
</pre></li>
<li><p>As with the <code>index.html</code> file, 
do not modify the generated 
<code>app.js</code> file.</p> 

<p>Put your code in 
the <code>Application.js</code> file, in the <code>app/</code> 
directory. This is where you place your application’s startup 
code, including a <code>launch</code> method, which contains 
any code required to be run during the startup of your application.</p>
<p>In our code example, the <code>launch</code> function creates 
the application’s initial viewport, which is a simple panel with 
a title and content:</p>
<pre>
Ext.define('MyApp.Application', {
    name: 'MyApp',
    extend: 'Ext.app.Application',
    launch: function() {
        Ext.create('Ext.container.Viewport', {
            layout: 'fit',
            items: [
                {
                    title: 'Hello Ext',
                    html : 'Hello! Welcome to Ext JS.'
                }
            ]
        });
    }
});
</pre>
</li>
</ol>

<a name="FurtherReading"></a>
## Further Reading

 - [Class System](#/guide/class_system)
 - [MVC Application Architecture](#/guide/application_architecture)
 - [Layouts and Containers](#/guide/layouts_and_containers)
 - [Workspaces in Sencha Cmd](#!/guide/command_workspace)
 - [Working with Data](#/guide/data)
 - [Ext JS SDK Download](http://www.sencha.com/products/extjs/)
 - [Sencha Forums](http://www.sencha.com/forum/)
