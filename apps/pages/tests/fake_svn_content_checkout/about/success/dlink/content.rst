========================================================
D-Link Australia Uses Python to Control Firmware Updates
========================================================

:Category: Business
:Keywords: Firmware, Service, USB, Serial, Hardware Control, Network
:Title: D-Link Australia Uses Python to Control Firmware Updates
:Author: How Wong
:Contact: grandsonata at aol dot com
:Date: 2007/08/02 10:00:00
:Web site: http://www.dlink.com.au/
:Summary: D-Link Australia uses Python to control firmware updates performed for warranty services and realizes an eight-fold increase in its upgrade capacity.
:Logo: .. figure:: dlink-logo.gif

Introduction
------------

D-Link Australia's RMA department provides warranty services to Australiasia.
Warranty services consist of diagnosing, fixing, testing, refurbishing, and
packaging security cameras, modems, voip hardware, switches and router
products.

Problem Description
-------------------

Prior to the development of the software described below, the standard method
of upgrading firmware during warranty service was to load settings and firmware
onto a modem through a web browser, after complete bootup of the firmware. With
this technique only one modem could be upgraded at a time by each machine. To
confirm successful upgrade of the firmware, the modem had to be rebooted and
the version checked, again through a web browser.

Modems with firmware corruption, those that needed to be converted to a
different localization region, and those that required an upgraded boot loader
could not be handled this way. Instead, a separate executable was used to
recover or convert at the boot-ROM level. On a typical day, there were
hundreds of these requiring service, with many different models.

The Solution
------------

To solve some of these problems, I started using a terminal script to drive
serial communication to the modems, in order to bypass manual use of the web
browser in the process of upgrading the firmware at the boot-ROM level, and
to reduce the required number of boots of the modem down to one. Although this
method eliminated many of the problems, there still remained the manual step of
selecting firmware appropriate to the modem's model and using different
commands for different boot loaders. Furthermore, only a single upgrade could
be performed at a time. It was not a particularly user-friendly solution.

To improve the situation, I decided to develop custom software to handle the
upgrades. I started by considering Java for performance but once I looked at
the complex Java serial communication code and the language itself I chose
Python instead. I was not a programmer and I felt I was not going to be able
work with and understand Java code. I believed Python would allow me to focus
more on the problem rather than the language.

DSL Firmware Recovery System
----------------------------

The development environment used for this work was Eclipse on Linux, using the
pySerial module, tftp, and PyQt3. The hardware contained quad port serial and
network cards and an RS-232 to TTL Serial interface that supports carrier
detect.

The components of the software system were the network module, serial I/O
module, a thread manager, and the GUI. A port manager detected online and
offline modems, and managed connecting and freeing ports. Each thread handled
one modem, connecting the network and serial interfaces. Once a modem was on,
the serial buffer was continuously monitored and any common error would be
detected. The correct firmware and settings files needed for each model's
upgrade were picked up by the software system. FTP commands were used to
control flashing memory regions and serial commands were used to control the
boot process. Running processes displayed their status through the easy-to-read
graphical and log user interface. The user interface also provided simple
controls to start, stop, and select models for the modems.

.. figure:: recovery-screen-small.jpg
   :alt: DSL Firmware Recovery System user interface
   
   *The DSL Firmware Recovery System's user interface, showing the system
   in the process of upgrading four modems simultaneously* `Zoom in`__
   
__ recovery-screen.jpg

The threading model was the most difficult to develop part of the software. I
used the threading support provided by Qt, and found it easier to use than
Python's threading module. When the main Qt program quits, it also automatically
quits any qthreads that are still running.

Results
-------

The project was a success. I was the sole creator and developer and was amazed
at the results achieved in just over 1,200 lines of code. It took 2-3 months to
develop the system, including testing.

Once completed, the DSL Firmware Recovery System was 8x faster on a single
machine, and it made it possible to add additional machines and serial cards
more easily. One day 1,600 modem firmware conversions were done, in addition
to the normal daily workload.

The software also helped to prevent errors, so that the quality of service
increased, and fewer defective modems were shipped out.

Conclusion
----------

Although I was without programming experience, Python allowed me to
simultaneously learn a programming language and accomplish a complex job.
Python is a uniquely powerful and usable "learn-as-you-go feature-rich
language."

Author
------

How Wong previously failed University programming and now works as a Linux
technologist. He is interested in using Linux and open-source software to solve
real world problems. Mr. Wong developed skills in the course of a varied IT
career and in his spare time working in Python and web programming,
multimedia, and Linux OS.

