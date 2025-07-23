#!/bin/bash
# Called by motion detection when an event ends

mosquitto_pub -t homeassistant/camera/living_door/motion -m 'OFF'
