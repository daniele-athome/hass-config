# My Home Assistant configuration

> I'm preparing my setup for the world to see. Stay tuned.

This is a mirror of my home automation configuration for Home Assistant.
It's been stripped down of some templates for speech and notifications.

## What's a Smart Home for me

My key principles for home automation are:

* Home automation should not get in the way of living my place naturally
* My place should know what I need before I do something about it
* Any automation or behavior should be overridable if needed
* Use only open source or flashable hardware
* My place should continue to work without Internet connection
* Use cloud services only when absolutely necessary

I'm always hungry for new ideas about automations, integrations and hardware.
Please us [my Home Assistant forum thread](...) if you want to contact me or
need help understanding or using any part of my configuration.

## Smart Home diagram

TODO some nice diagram with draw.io maybe

## Hardware used

* An unused 2012 laptop running Home Assistant and Rhasspy
* ConBee II ZigBee USB controller attached to the laptop
* Raspberry Pi 3B+ running Kodi
* A cheap Android tablet as my control center
* Google Home (used only as speaker)
* Sonoff Basic flashed with Tasmota
* Shelly One flashed with Tasmota
* ZigBee Aqara temperature sensors
* ZigBee Aqara motion sensor
* ZigBee Aqara door sensor
* ZigBee RGB LED strips

TODO also include a wishlist or planning to buy

## Lovelace interface

I view this mainly from my tablet hanging on a wall. I had to take some measures
to make it work on the tablet because a complex web application like Lovelace
really needs computing power and memory (did I say it's a cheap tablet?).
A few tricks to keep it fast:

* Don't use a background image
* Don't use animated icons
* Don't put too many cards on a view

I tried pretty much every browser on the tablet and the fastest seems to be Chrome.

My views are pretty tailored to my tablet display: I made them so all content
would fit and I wouldn't need to scroll up and down.

### Main view/Home
![Home](lovelace-home.png)

### Environment/HVAC
![Environment](lovelace-environment.png)

### System monitor
![System](lovelace-system.png)

### Home automation devices
![Things](lovelace-things.png)

### Security
![Security](lovelace-security.png)

## Software setup

All software is installed through hand-crafted Ansible recipes. Home Assistant runs on
Debian GNU/Linux using a virtualenv.

## Packages

Organizing Home Assistant configuration is **hard**. Really, when the number of
automations and sensors starts growing, organizing everything becomes a bit like
doing architecture design for a piece of software. So, if you have any idea you'd
like to share about that, feel free to write to me on the Home Assistant forum.

### Assistant

Meet **Karen**, my voice assistant made with [Rhasspy](https://github.com/synesthesiam/rhasspy).
HASS receives intents from Rhasspy which are processed by doing something
and speaking some reply. No conversations support yet. What my voice commands
can do:

* say date or time
* get weather/environment information (temperature, some forecasts)
* play some music from my media center
* start a countdown
* commute traffic information
* good morning/good night with some useful actions for morning and night

I use my own wake word &mdash; trained on my own dataset &mdash; and a
ReSpeaker microphone array to listen for voice commands. I might publish my
Rhasspy configuration one day.

### Calendar

Just a few calendar sensor. Nothing really useful by itself, it's just data
used by other automations elsewhere.

### Devices

Definitions for some smart devices and device trackers, including phones. It
also includes some automations for notifying about low battery levels.

### Environment

House environment sensors (temperature, humidity) and an automation that alerts
me if the house is on fire :fire:

### Firmware

Firmware update notifications.

### HVAC

Integration with [my homemade thermostat](https://github.com/daniele-athome/thermorasp-docs).

### Lights

Some smart light entities and a few scenes that are used in automations elsewhere.

### Media Player

Some fun with my media players:

* Kodi on a Raspberry PI
* Philips TV set
* Google Home (used only for Karen's voice)

It contains mainly utility scripts for handling those players and a few sensors
that help some automations elsewhere.

### Other

I didn't know where else to put these.

### Persons

Known people living at my place (just me for now).

### Presence

I use a combination of sources to determine my presence:

* Network (nmap integration)
* Bluetooth using [monitor](https://github.com/andrewjfreyer/monitor/)
* GPS using [GPSLogger](https://gpslogger.app/)

When my entrance door opens, some lights are turned on if needed and a presence
arrival scan is initiated. When my phone is detected, Karen greets me and tells
me some information about the house. Also, the alarm system is disarmed.

When I leave, a deperture scan is initiated. When my phone is no longer detected,
lights and any media player are turned off. The alarm system is armed.

Since both automations are triggered by the entrance door sensor, I use a
combination of conditions to distinguish between arrival and departure.

During the night, a motion sensor will turn on a LED strip with a mild light
to help me moving through the living room.

### Scenarios

A few nice automations here. Not all lights are under Home Assistant control yet
though.

Scenarios are mainly for my living room, since is the room where most of my home
automation hardware is installed at the moment.

When I watch something, all lights are turned off &mdash; I call this *cinema mode*.
A LED strip facing my ceiling is gently turned on when I pause.

Cinema mode is suspended if I ask Karen to keep some lights on &mdash; very useful
when I'm watching something while eating &mdash; I do that a lot :spaghetti:

Controlled lights are turned off automatically when too much light is detected in
the room.

#### Guest mode

I need to improve this, but mainly it does something when I tell Karen that I have
guests:

* set a specific light scene
* put some ambient playlist on ([ThePianoGuys](https://www.youtube.com/channel/UCmKurapML4BF9Bjtj4RbvXw)!!)
* Karen won't speak unless it's an emergency

### Security

My home-made security system, based on a webcam and a few other sensors. Tightly
integrated with presence information, my alarm system is armed when I leave
and is disarmed when I'm back. No need to think about it, ever.

### System

My system is made up of a few running machines. This is a how a keep an eye on
them. Heavy use of [Glances](https://github.com/nicolargo/glances/).

### Theme control

Just an automation for setting my preferred theme on startup:
[Google Dark Theme](https://github.com/JuanMTech/google_dark_theme) by
[@JuanMTech](https://github.com/JuanMTech).

### Weather

Some sensors for weather information in my area.

### Zones

Home and work :-)

## Copyright

<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a>  
This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.
