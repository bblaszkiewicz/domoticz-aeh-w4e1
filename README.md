# Hisense AC (AEH-W4A1) - Domoticz Python plugin
**Domoticz Python plugin for Hisense AC (AEH-W4A1)**

## Information
 - *This plugin is based the [Library for Hisense AEH-W4A1](https://github.com/bannhead/pyaehw4a1) by Davide Varricchio. Thank you very much for your work.*
 - *Python I see for the third time in my life, I write on it for the first time. If there is a person who will bring the ugliness that I wrote to a normal form I will be very grateful.*
 - *Written this under beer and heavy metal. So, it comes with ABSOLUTELY NO WARRANTY. :)*
  
### Domoticz settings
See this [link](https://www.domoticz.com/wiki/Using_Python_plugins) for more information on the Domoticz plugins.

* SSH to your server on which Domoticz is installed *
* Enter the following commands *
```bash
cd domoticz/plugins
git clone https://github.com/x-th-unicorn/domoticz-aeh-w4a1.git
```
* When updating to the latest version on Github enter the following commands*
```bash
cd domoticz/plugins/domoticz-aeh-w4a1
git pull
```
* Restart the Domoticz service
```bash
sudo service domoticz.sh restart
```

* Now go to **Setup**, **Hardware** in your Domoticz interface. There you add
**Hisense AC (AEH-W4A1)**.

Make sure you enter all the required fields.

| Field | Information|
| ----- | ---------- |
| IP address | Enter the IP address of your AC (see instructions above how to find the IP address, also make sure it is static) |
| Update interval | Enter the update interval in seconds, this determines with which interval the plugin polls the AC |
| Debug | When set to true the plugin shows additional information in the Domoticz log |

After clicking on the Add button the devices are available in the **Switches**, **Temperature** and **Utility** tabs.

## Confirmed working on the following AC´s
- [x] Ballu BSAGI-09HN1-17Y-01

# Support the project
If the plugin was useful to you and you want to thank the author, you can send me a couple of bucks on coffee or on beer :)  
And sorry for my lousy English  
  
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/xthunicorn)  