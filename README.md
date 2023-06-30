# HA_Network_Storage_Backup
Home Assistant backup automation on network storage

## Table of contents
* [Decription](#decription)
* [Setting up the network storage](#setting-up-the-network-storage)
* [Package installation](#package-installation)
* [Frontend Custom Card](#frontend-custom-card)

## Decription

This package allows for the automation of Home Assistant backup to network storage, a functionality introduced in version 2023.6.

## Setting up the network storage

AAAA

## Package installation

AAA

## Frontend Custom Card

The entities created in the package can be displayed on a custom card that allows for backup management:
* Perform manual backup
* Enable/disable automatic backup
* Set backup schedule
* Set the day or days of the week to perform the backup
* Set the delay for checking the completion of the backup (time depends on the backup size)
* Display the status of the backup execution

```
entities:
  - label: Impostazioni
    type: section
  - entity: input_button.execute_backup
  - entity: input_boolean.auto_backup
  - entity: input_datetime.backup_time
  - entity: input_select.backup_day
  - entity: input_number.ritardo_backup_check
  - entity: input_text.backup_status
icon: mdi:cloud-upload-outline
show_header_toggle: false
title: Home Assistant Backup
type: entities
state_color: true
```

![alt text](https://github.com/paolo-hub/HA_Network_Storage_Backup/blob/main/images/home_assistant_frontend_card.png)
