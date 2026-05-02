# BMS Protocol Probe Tool

Structured brief imported from product requirements. See repository history/conversation for full version.

## Goal
Build a **safe read-only** BMS protocol probe utility with:
- passive listen
- active safe probe (read-only)
- protocol scoring
- basic decoding
- JSON/TXT/RAW reports

## MVP constraints
- No write/control commands in autodetect.
- Blocklist enforcement is mandatory.
- Start with RS485 serial workflows and Pylon LV / JK Pylon profiles.
- CAN remains a stub in MVP.
