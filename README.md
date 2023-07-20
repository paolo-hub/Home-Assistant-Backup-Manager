# Home Assistant Backup Manager
## Please wait: under construction

![alt text](https://badgen.net/badge/release/v.1.0/green?) ![alt text](https://badgen.net/badge/platform/HomeAssistant/blue?) ![alt text](https://badgen.net/badge/required/Supervisor/red?) ![alt text](https://badgen.net/badge/code/yaml/pink?) ![alt text](https://badgen.net/badge/license/GPL-3.0/orange?)

Home Assistant backup manager, both locally and on network storage.

## Table of contents
* [Description](#description)
* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Frontend Custom Card](#frontend-custom-card)
* [Credits](#credits)

## Description

This package allows you to manage the backup of Home Assistant. You can schedule full or partial backups, either alternatively or concurrently. For example, you can schedule a full backup once a week and a backup of Home Assistant istance only once a day.

The partial backup manager allows you to choose which elements to include in the backup, such as add-ons and system folders. The backup process is monitored, and you can receive system notifications and Pushover notifications indicating the successful completion or failure of the backup.

In addition to managing the settings and automatically creating backups, you can also decide how many backups to keep, giving you control over the total size of the backup archive. This package also provides information about the latest available backup, such as its name, date, and type.

The backup is created in the default location set in Home Assistant, which means it can be done locally, as the default setting, or on network storage, a feature available from Home Assistant version [2023.6](https://www.home-assistant.io/blog/2023/06/07/release-20236/#connect-and-use-your-existing-network-storage)

## Prerequisites

* Supervisor: [See Home Assistant official page](https://www.home-assistant.io/integrations/hassio/)
* Pakages: [See Home Assistant Package integration page](https://www.home-assistant.io/docs/configuration/packages/)
* PushOver notification service: [See the Home Assistant Pushover intagation page](https://www.home-assistant.io/integrations/pushover/)
* Shell Access, for example with SSHCommand Add-On available trought HACS [See the GitHUB repository page](https://github.com/AlexxIT/SSHCommand)

## Installation
### Package Installation
This package is composed of three elements:

* The package it self: _pkg_backup_home_assistant.yaml_
* A script: _backup_remove.sh_
* Configuration for the Home Assistant frontend: _ha_backup_frontend.yaml_

To install the package, you need to use the first two files, while the third one is prepared for management.

To proceed with the installation:
1. Download the repository.
2. Copy the file _pkg_backup_home_assistant.yaml_ to the packages folder, for example, _/config/packages_.
3. Copy the script _backup_remove.sh_ to the configurations folder, _/config_.
4. Make the script executable by accessing the Home Assistant CLI, for instance, through SSHCommand Add-On, and execute as the root user:
```
chmod +x backup_remove.sh
```
5. Restart Home Assistant.
6. Create a new card in the Home Assistant frontend and paste the content of the _ha_backup_frontend.yaml_ file into it.


### Network Storage Backup
The backup is executed in the default destination folder of Home Assistant.

The basic setting involves local backup creation, but it's possible to move the storage externally to a remote destination connected via SMB or NFS.
To do this, you need to configure the remote location in _Settings > System > Storage_.

In the configuration screen, select _"Backup"_ as the use of storage and fill in the data for accessing the remote share. Once the settings are saved, the connection to the new backup destination will be established.

To verify that it has been set as the default one, go to _Settings > System > Backups_ and from the three-dot menu in the upper right corner select "Change default backup location."
Then, from the dropdown list, choose the location created with network storage



## Frontend Custom Card

The entities created in the package can be displayed on a custom card that allows for backup management:
* Perform manual backup
* Enable/disable automatic backup
* Set backup schedule
* Set the day or days of the week to perform the backup
* Set the delay for checking the completion of the backup (time depends on the backup size)
* Display the status of the backup execution



![alt text](https://github.com/paolo-hub/Home-Assistant-Backup-Manager/blob/main/images/Basic%20Frontend.jpg)

![alt text](https://github.com/paolo-hub/Home-Assistant-Backup-Manager/blob/main/images/Detailed%20Frontend.jpg)

![alt text](https://github.com/paolo-hub/Home-Assistant-Backup-Manager/blob/main/images/Full%20Backup%20Settings.jpg)

![alt text](https://github.com/paolo-hub/Home-Assistant-Backup-Manager/blob/main/images/Partial%20Backup%20Settings.jpg)

![alt text](https://github.com/paolo-hub/Home-Assistant-Backup-Manager/blob/main/images/Retained%20Backup%20Settings.jpg)

## Credits

I received support from the [HassioHelp](https://t.me/HassioHelp) community in the development of this package, and I would like to express my gratitude to them.
