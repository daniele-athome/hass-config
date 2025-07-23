#!/bin/bash
# Called by motion detection when an event starts

mosquitto_pub -t homeassistant/camera/living_door/motion -m 'ON'
