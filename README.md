# Home Assistant Network Storage Backup

![alt text](https://badgen.net/badge/release/v.1.0/green?) ![alt text](https://badgen.net/badge/playform/homeassistant/blue?) ![alt text](https://badgen.net/badge/code/yaml/orange?)

Home Assistant backup automation on network storage.

## Table of contents
* [Decription](#decription)
* [Prerequisites](#prerequisites)
* [Setting up the network storage](#setting-up-the-network-storage)
* [Package installation](#package-installation)
* [Frontend Custom Card](#frontend-custom-card)

## Decription

TStarting from Home Assistant version 2023.6, the new network storage feature is available. This package automates the creation of Home Assistant backups on a dedicated and shared network storage from an external server. It also monitors the execution of backups and notifies the status using the popular Pushover service and the built-in notification system in Home Assistant.

## Prerequisites

* Pakages: [See Home Assistant Package integration page](https://www.home-assistant.io/docs/configuration/packages/)
* Folder Watcher integration: [See the Home Assistant Folder Watcher integration page](https://www.home-assistant.io/integrations/folder_watcher/)
* PushOver notification service: [See the Home Assistant Pushover intagation page](https://www.home-assistant.io/integrations/pushover/)

## Setting up the network storage

AAAA

## Package installation

AAA

```
#########################################################
# BACKUP FOLDER:
      key: &bk_folder
        /share/backup_on_miniserver   
#########################################################
```

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

![alt text](https://github.com/paolo-hub/HA_Network_Storage_Backup/blob/main/images/home_assistant_backup_card.png)
