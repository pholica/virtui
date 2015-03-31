#virtui

Command line tool aiming for easy management of virtual systems in libvirt.

##Features

Virtui can currently perform following actions with VMs:
* start
* stop (send acpi event)
* force stop (unplug power)
* soft reboot (send acpi event)
* hard reboot (reset sent directly to CPU)
* open serial console
* launch viewer for VM
* change CD/DVD if VM has drive
* launch ssh (if VM is on same host as virui)
* vnc (if VM is on same host as virui)

###ssh, vnc and network
Since virtui has very limited knowledge (same as virt-manager and possibly other tools) about network and only knows MAC addresses of the VM. So virtui looks into ARP table if there is record of MAC address owned by VM and has correspondig IP address. In such case, virtui offers such IP address for the user and is able to launch ssh and vnc for such VM.

###configuration


###helper scripts


##Other notes

###Policykit

If you're using distribution with policykit, first thing you probably want to do is to permit all users within one group to manage virtual systems.
This can be done by following policykit rule into file `/etc/polkit-1/rules.d/10-libvirt.rules`.
```javascript
polkit.addRule(function(action, subject) {
    if (action.id == "org.libvirt.unix.manage" && subject.isInGroup("wheel")) {
	return polkit.Result.YES;
    }
});
```
