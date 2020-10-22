# Pugdebug

pugdebug is a standalone debugging client for PHP applications that uses Xdebug as the debugging engine.

A python 3.5, PyQt5 project.

**NOTE**: I am maintaining a fork!

## Install pugdebug

### Install from pip

`pip install pubdebug`

### Install from source

`pip install -r requirements.txt`

## Using pugdebug

`./app.py`

## Settings

To bring up the `Settings` window, navigate to `Files -> Settings` (shortcut: `Ctrl+S`).

### Path settings

The `Path` section refers to the path settings.

The `Root` under the `Path` section is the root path where the project you want to debug is located.

The `Maps from` under the `Path` section is for when the project you want to debug is under a virtual machine, like Vagrant. Here you would enter the path of the project under that VM.

For example, if a project I'm working on is in `/home/robert/wwww/pugdebug` and that maps to `/var/www` under the VM, the `Root` would be set to `/home/robert/www/pugdebug` and the `Maps from` would be set to `/var/www`.

### Debugger settings

The `Host` setting should be the IP address of the machine on which pugdebug runs. In most cases (like vagrant) it is perfectly fine to leave this field blank.

The `Port` setting is the port number on which Xdebug will attempt to connect to the machine on which pugdebug runs. The default port is `9000`.

The `IDE Key` setting allows to filter out messages from Xdebug based on this value.

`Break at first line` tells the debugger should it break on the first line or not (on CMS is better to disable it).

`Max depth`, `Max children` and `Max data` settings control the amount of information about variables is retrieved from Xdebug.

## Hotkeys

* `F1` - Start Listening
* `F2` - Stop Listening
* `F3` - Stop
* `F4` - Detach
* `F5` - Run
* `F6` - Step Over
* `F7` - Step In
* `F8` - Step Out
* `Ctrl+N` - New project
* `Ctrl+F` - Search
* `Ctrl+T` - Search for file
* `Ctrl+G` - Go to line
* `Ctrl+S` - Show settings
* `Alt+F4` - Exit application

## FAQ

### Debugging sessions

To start debugging, click the `Start listening` button in the top left corner.

pugdebug then listens to all connections on the `Port` provided, and if the connection has the `IDE Key` matching with what is configured, it will start debugging the PHP request from that connection.

In the case if there is already a debugging in progress, the new connection will be queued and once the debugging of the current connection is done, the new one will be debugged.

This allows pugdebug to debug multiple requests (think ajax).

Load a web project in a browser and start a [HTTP debugging session](http://xdebug.org/docs/remote#browser_session).

pugdebug should pick up that request and display the index file of the web project, while stopping the execution on the first line.

Using the `Run`, `Over`, `In`, `Out` continuation commands allows stepping through the PHP code.

Setting breakpoints is possible by double clicking the line where a breakpoint is needed.

The correspoding line number should be highlighted and a new breakpoint should be listed in the breakpoint viewer (bottom right corner).

Double clicking the line with a breakpoint should remove that breakpoint.

The `Stop` action will stop debugging the current request and tell Xdebug to stop further execution of the PHP script that is being debugged.

The `Detach` action will detach the debugger from the current request, which allows to stop debugging but also let the PHP script finish as it normally would.

The `Stop listening` action will tell pugdebug to stop listening to new incomming connections.

### Setting up Xdebug

There is a wiki page with [simple examples of Xdebug configurations](https://github.com/robertbasic/pugdebug/wiki/Setting-up-Xdebug) that should help with setting up Xdebug for remote debugging.

### Setting up the development environment

Setting up the development environment should be needed only when you want to help out with developing pugdebug itself. 

The main dependencies are Python 3.7, [QT5](http://doc.qt.io/qt-5/gettingstarted.html), [SIP](http://www.riverbankcomputing.com/software/sip/download) and [PyQt5](http://www.riverbankcomputing.com/software/pyqt/download5).

### WordPress

As WordPress uses a hook system *Break on the first line* can create issues because open the first file and not where it is the breakpoint as example, so it is better to disable that option.