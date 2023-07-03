# Home Assistant Network Storage Backup
## Please wait: under construction

![alt text](https://badgen.net/badge/release/v.1.0/green?) ![alt text](https://badgen.net/badge/playform/HomeAssistant/blue?) ![alt text](https://badgen.net/badge/code/yaml/pink?) ![alt text](https://badgen.net/badge/license/GPL-3.0/orange?)

Home Assistant backup automation on network storage.

## Table of contents
* [Description](#description)
* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Setting up the network storage](#setting-up-the-network-storage)
* [Enable the folder watcher integration](#enable-the-folder-watcher-integration)
* [Package installation](#package-installation)
* [Frontend Custom Card](#frontend-custom-card)
* [Credits](#credits)

## Description

Starting from Home Assistant version 2023.6, the new network storage feature is [available](https://www.home-assistant.io/blog/2023/06/07/release-20236/#connect-and-use-your-existing-network-storage). This package automates the creation of Home Assistant backups on a dedicated and shared network storage from an external server. It also monitors the execution of backups and notifies the status using the popular Pushover service and the built-in notification system in Home Assistant.

## Prerequisites

* Pakages: [See Home Assistant Package integration page](https://www.home-assistant.io/docs/configuration/packages/)
* Folder Watcher integration: [See the Home Assistant Folder Watcher integration page](https://www.home-assistant.io/integrations/folder_watcher/)
* PushOver notification service: [See the Home Assistant Pushover intagation page](https://www.home-assistant.io/integrations/pushover/)

## Installation

The installation of this package does not require the use of additional components.

### Setting up the network storage

AAAA

### Enable the folder watcher integration

To activate the folder watcher integration, you need to add the following lines to /config/configuration.yaml:

```
folder_watcher:
  folder: /path/to/network/storage/folder
  patterns:
    - '*.tar'
```

In the above configuration, you specify the location of the network storage folder and indicate the *.tar format, which is the backup archive format.

### Package installation

Download the package from the resources and copy it to the /config/packages folder. Afterward, modify the path of the network storage folder.

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


## Credits

I received support from the [HassioHelp](https://t.me/HassioHelp) community in the development of this package, and I would like to express my gratitude to them.
