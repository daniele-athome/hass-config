# My Home Assistant configuration

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
You may visit [my Home Assistant forum thread](https://community.home-assistant.io/t/daniele-athome-my-home-assistant-configuration/181754)
if you want to contact me or need help understanding or using any part of my configuration.

## Smart Home diagram

### Home automation view

TODO home automation view diagram

### Technology view

![Technology diagram](technology-view.png)

## Hardware used

* An unused 2012 laptop running Home Assistant and Rhasspy
* Home Assistant Connect ZBT-1 USB controller attached to the laptop
* Raspberry Pi 4B running Kodi
* A cheap Android tablet as my control center
* Google Home (used only as speaker)
* Bosch Thermostat II
* Sonoff Basic flashed with Tasmota
* Shelly 1 (some with native firmare, some with Tasmota)
* Xiaomi Mi Bluetooth LE sensors
* ZigBee Aqara temperature sensors
* ZigBee Aqara motion sensors
* ZigBee Aqara door sensor
* ZigBee RGB LED strips
* Custom desk radio (Raspberry Pi Zero W + Pimoroni Pirate Audio)

> TODO also include a wishlist or planning to buy

## Lovelace interface

I view this mainly from my tablet hanging on a wall. I had to take some measures
to make it work on the tablet because a complex web application like Lovelace
really needs computing power and memory (did I say it's a cheap tablet?).
A few tricks to keep it fast:

* Don't use a background image
* Don't use animated icons
* Don't put too many cards on a view

The native Home Assistant app seems to work well enough.

My views are pretty tailored to my tablet display: I made them so all content
would fit and I wouldn't need to scroll up and down.

### Main view/Home

![Home](lovelace-home.png)

### Environment/HVAC

![Environment](lovelace-environment.png)

### System monitor

![System](lovelace-system.png)

### Home automation devices

> I'm refactoring some stuff so not all devices are reporting their status yet.

![Things](lovelace-things.png)

### Network monitor

![Network](lovelace-network.png)

## Software setup

All software is installed through handcrafted Ansible recipes. Home Assistant runs on
Debian GNU/Linux using a virtualenv.

## Packages

Organizing Home Assistant configuration is **hard**. Really, when the number of
automations and sensors starts growing, organizing everything becomes a bit like
doing architecture design for a piece of software. So, if you have any idea you'd
like to share about that, feel free to write to me on the Home Assistant forum.

### Assistant

I use the built-in Assist feature in Home Assistant and often experiment with different
voice recognition and hardware (I've been trying Voice Preview lately, it works really
well if you use the well-trained wake words and a cloud speech-to-text service).

Speech templates for the assistant lives in a specific directory that I won't publish.
To introduce some sense of "nuisance" in sentences, I created multiple versions for
each type of sentence to be spoken. Templates are used by the Assistant Speak app
in `apps/assistant_speak.py`.

### Alarm clock

A simple alarm clock synced with the alarm clock I set on my phone. My favorite radio station
is streamed through a home-made speaker in my bedroom.

### Calendar

Just a few calendar sensor. Nothing really useful by itself, it's just data
used by other automations elsewhere.

### Chores

A very rough and very home-made chores management package. Mainly vacuum robot automations and chores tracking.

### Devices

Definitions for some smart devices and device trackers, including phones. It
also includes some automations for notifying about low battery levels.

### Environment

House environment sensors (temperature, humidity), HVAC automations and scripts.

### Firmware

Firmware update notifications.

### House mode

Configuration data and some automations for what I call the *house mode*. Basically it's the current state of my home.
Each state represents specific behaviors that my place will have, automations to be enabled, stuff to turn on and off,
and so on. The house mode input_select is used throughout the packages.

### Lights

Some light entities and a few scenes that are used in automations elsewhere.

### Media Player

Some fun with my media players:

* :cinema: Kodi on a Raspberry PI
* :tv: LG TV set
* :speaker: Google Home (used only for Assist voice)
* :musical_note: House music system powered by Mopidy and Snapcast

It contains mainly utility scripts for handling those players and a few sensors that
help some automations elsewhere. Interactions between media players are also handled
here (e.g. pause music when playing videos on Kodi and vice versa).

### Night mode

A *house mode* for the night. It is an environment state where:

* all lights are off
* all media players are off
* my media server is suspended
* no assistant warnings are fired unless it's an emergency
* I'm sleeping :)

Night mode can be triggered manually by saying goodnight to Karen. Otherwise, starting 23:00, Home Assistant will check
every minute that:

* all lights are off
* all media players are off
* no motion but in bedroom
* no light everywhere
* my phone is charging
* my notebook is turned off or idle

Those are my very personal conditions for which I can be declared sleeping or going to sleep.
If all those conditions are met, Home Assistant will start a 3 minutes timer and send a push notification to my phone
warning me that night mode is about to be activated. The notification will have 3 actions:

1. Snooze: delay night mode for 15 minutes (after 12 minutes another notification will be sent)
2. Enable now: enable night mode immediately
3. Cancel: disable night mode for tonight

If no action is taken, night mode will be enabled automatically after the timer expires.

### Presence

I use a combination of sources to determine my presence:

* Network from nmap and Mikrotik integrations
* Bluetooth using [monitor](https://github.com/andrewjfreyer/monitor/)
* GPS from the Home Assistant app

When my entrance door opens, some lights are turned on if needed and a presence
arrival scan is initiated. When my phone is detected, Assist greets me and tells
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

Most scenarios are for my living room, since is the room where most of my home
automation hardware is installed at the moment.

When I watch something, all lights are turned off &mdash; I call this *cinema mode*.
A LED strip facing my ceiling is gently turned on when I pause.

Cinema mode is suspended if I ask Karen to keep some lights on &mdash; very useful
when I'm watching something while eating &mdash; I do that a lot :spaghetti:

Controlled lights are turned off automatically when too much light is detected in
the room.

The bedroom has an experimental time-of-flight sensor at the side of the door that
can detect passage (and direction!). It is used to turn off and on the main light
or the bed light, depending on the time of day. The bedroom speaker is also controlled
by this automation (no need to play anything if nobody is in the room).

I try to keep room-related configuration in their respective `scenario_<room>.yaml`
files.

#### Guest mode

I need to improve this, but mainly it does something when I tell Assist that I have guests:

* set a specific light scene
* put some ambient playlist on ([ThePianoGuys](https://www.youtube.com/channel/UCmKurapML4BF9Bjtj4RbvXw)!!)
* Assist won't speak unless it's an emergency

### Security

My home-made security system, based on a webcam and a few other sensors. Tightly
integrated with presence information, my alarm system is armed when I leave
and is disarmed when I'm back. No need to think about it, ever.

### System

My system is made up of a few running machines. This is a how a keep an eye on
them. Heavy use of [Glances](https://github.com/nicolargo/glances/).

## AppDaemon

I use AppDaemon mainly for my assistant. Basic question-answer skills are handled
directly in Home Assistant, but more complex stuff required some coding, so I've
implemented a few apps for those.  

## Acknowledgements

Many people helped me through this, either by sharing their own configurations
or by replying to my calls for help on the Home Assistant forum. **Publishing my
work is a way to thank those people and to give back to this great community.**

## Copyright

<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a>  
This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.
