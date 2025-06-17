---
id: 3821
title: 'Installing Debian on a Mac Mini G4'
date: '2015-10-09T21:06:06-07:00'
author: cjtrowbridge
layout: post
guid: 'http://cjtrowbridge.com/?p=3821'
permalink: /2015/10/09/turn-a-mac-mini-g4-into-a-xen-hypervisor/
categories:
    - Projects
---

This post is part of a larger series about [Building a Cloud at Home For Free](http://blog.cjtrowbridge.com/2015/10/04/building-a-cloud-at-home-for-free/) as part of building scalable web applications from the ground up. Here we are focusing specifically on installing Debian an old G4 Mac Mini. If you are trying to setup Debian in a virtual server inside Windows, check out my post [Installing Virtualbox and Debian on Windows 10](http://blog.cjtrowbridge.com/2015/10/04/installing-virtualbox-and-debian-on-windows-10/). I work at a tech support company and I recently came upon a Mac Mini G4 for free which had been discarded at work as no one wanted it. At this point it was about ten years old and did not support any of the new software. I found some spare parts around the shop that were compatible and maxed out all its resources. Here's what I ended up with;

<div>![apple_mac_mini_g4](http://blog.cjtrowbridge.com/wp-content/uploads/2015/10/apple_mac_mini_g4.jpg)  
- **CPU:** 1.5ghz G4
- **RAM:** 1gb ddr
- **HDD:** 80gb pata

 </div>This may not sound like much, but it's more than enough to run Debian! My research made it clear that the right Linux distribution was going to be Debian for PowerPC. This version would work on this computer and support all the things I had in mind for it. Go over to the [Debian Repository](https://www.debian.org/CD/) and grab the first CD of the most recent distro for "PowerPC." Torrents are usually the fastest way to get them! ### Booting To Debian Installer On The Mac

The trickiest part was figuring out how to get Debian onto the Mac Mini. The key turned out to be burning the ISO to a CD instead of trying to boot from USB as this is not supported. Also, the file system was not supported by most of the usual ISO burning tools I usually use. The only one I found that could handle burning this image's filesystem with a working bootloader was ImgBurn which is available in [Ninite](http://ninite.com). Burn that CD and put it in the Mac's optical drive. The first time you power on the Mac, you need to clear the "PRAM" which will prevent your new installation from booting afterwards. Hold down Command+Option+P+R immediately after the boot sound. Hold it down until you hear the sound again. Then hold down just the C button to boot from your Debian for PowerPC CD. ### Installing Debian

Now it is basically just the normal setup process. Most of the installation process is pretty self-explanatory. Choose a language, timezone, keyboard layout, etc... It goes just like any OS install. I used the hostname lamp2 as part of my larger plan and roadmap for the greater project. I am forwarding a subdomain from my website to the server cluster, so I used that domain (projects.cjtrowbridge.com) but this step can be skipped if you do not intend to setup a publicly accessible server. And this can easily be changed later. Next setup your root password. This is the main administrative password for the "root" user account. Choose a [strong password](https://xkcd.com/936/) because this account has access to everything! Next up is your user account. This is the account you will use to log into the machine whenever you may don't need to do anything major that requires root access. Timezone is critical to many important technologies as well as to web application frameworks working correctly. You'd be surprised how often mistakes here will create issues. Now comes partitioning. I recommend sticking with the recommended setting of "Guided - Use Entire Disc" and then selecting just one single partition. Then it will ask you if you are sure. The default option is no, but choose yes to continue. The installer will ask if you want to scan another disc. Select No, it is not necessary. Then select Yes to using a network mirror and go with the default options, we will come back to this in a moment. It will download any necessary files which may take a few minutes. Here is the tricky part. It asks what you want the installer to setup for you. I recommend selecting ONLY "SSH Server" and "Standard System Utilities" from this menu. <center>![debian_install_2](http://blog.cjtrowbridge.com/wp-content/uploads/2015/10/debian_install_2-465x392.png)</center>*This image is of the installation happening inside windows. It is difficult to take screenshots on computers which do not have an OS installed yet, but it looks just like this!*The first step to setting up Debian is to log into the machine as root using the password you setup for your root account a moment ago. ### Setup a Static IP

Use the nano text editor to edit the network configuration file by executing the following command; <fieldset>```
nano /etc/network/interfaces
```

</fieldset>You will find something like this; <fieldset>```
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
allow-hotplug eth0
iface eth0 inet dhcp
```

</fieldset>Comment out the old settings for the primary network interfaces and add the new lines shown below. You will need to select an IP and use the correct gateway for your network; <fieldset>```
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
#allow-hotplug eth0
#iface eth0 inet dhcp

auto eth0
iface eth0 inet static
	address 8.0.0.11
	netmask 255.255.255.0
	gateway 8.0.0.1
```

</fieldset>Hold down control+x and then press y, then enter to save your changes. ### Enable SSH

Type the following command to get to the config file for SSHD, the service which allows you to remote into the terminal and access <fieldset>```
nano /etc/ssh/sshd_config
```

</fieldset>Find the line that says PermitRootLogin with-password and change it to; <fieldset>```
PermitRootLogin yes
```

</fieldset>### Setup a Static IP

Use the text editor nano to edit the network configuration file by typing the following command; <fieldset>```
nano /etc/network/interfaces
```

</fieldset>You will find something like this; <fieldset>```
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
allow-hotplug eth0
iface eth0 inet dhcp
```

</fieldset>Comment out the old settings for the primary network interfaces and add the new lines shown below. You will need to select an IP and use the correct gateway for your network; <fieldset>```
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
#allow-hotplug eth0
#iface eth0 inet dhcp

auto eth0
iface eth0 inet static
	address 8.0.0.11
	netmask 255.255.255.0
	gateway 8.0.0.1
```

</fieldset>Hold down control+x and then press enter to save your changes. Type the command "reboot" into the console to restart the server and apply the changes. ### Enable SSH

Type the following command to get to the config file for SSHD, the service which allows you to remote into the terminal and access <fieldset>```
nano /etc/ssh/sshd_config
```

</fieldset>Find the line that says PermitRootLogin with-password and change it to; <fieldset>```
PermitRootLogin yes
```

</fieldset>Save your changes. Enabling root remotely is potentially a security concern as someone could brute-force the password and have root access. So we need to install fail2ban to prevent this. If too many failed attempts are made, the remote user will be banned from attempting to log into the server. <fieldset>```
apt-get -y install fail2ban
```

</fieldset>### Set APT To Online-Only

We need to set the package manager to use the online-repositories only, so it won't be constantly asking us to insert the CD. Type out <fieldset>```
nano /etc/apt/sources.list
```

</fieldset>Find the line that starts with "deb cdrom"... Add a "#" at the beginning to comment it out, and then Ctrl+X to save! Simple as that. Now let's apply all our changes by typing the command "reboot" into the console to restart the server. Now you can use putty to connect securely to the server! At this point, I switch to putty as it is much easier to work with the server through putty with the ability to copy and paste commands. This is not possible when using the console directly. Putty is free software available through [Ninite](http://ninite.com) or from [putty's website](http://putty.org). At this point, I tried to install Xen from apt, but unfortunately it turns out this chip is not supported :\[ So for now, I completed the rest of the LAMP setup procedures detailed [here](http://blog.cjtrowbridge.com/2015/10/04/setting-up-debian-as-a-lamp-server/), and this is now just a normal Lamp Server.